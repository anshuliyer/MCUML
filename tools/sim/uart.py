#!/usr/bin/env python3
"""MCUML UART Streamer (uart.py).

Connects to UART streams from QEMU simulation or hardware targets.

Supports:
- TCP Client/Server (e.g. QEMU -serial tcp:127.0.0.1:5555,server,nowait)
- Unix Domain Socket (e.g. QEMU -serial unix:/tmp/uart.sock,server,nowait)
- Serial TTY / Hardware ports (via pyserial for real silicon or /dev/pts/*)
- Real-time bidirectional streaming with console & file logging
- Automated pattern matching / wait-for-pattern (--expect)
- Data/File streaming over UART (e.g. ML test vectors, model weights)
- Command-line interface with -h, --h, and --help support
- Python importable library (UartStreamer)
"""

from __future__ import annotations

import argparse
import os
import re
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional, Union

# Optional pyserial for hardware / tty devices
try:
    import serial  # type: ignore
    HAS_PYSERIAL = True
except ImportError:
    HAS_PYSERIAL = False


class UartStreamer:
    """Manages bidirectional UART streaming over TCP, Unix Sockets, or Serial devices."""

    def __init__(
        self,
        host: Optional[str] = "127.0.0.1",
        port: Optional[int] = 5555,
        device: Optional[str] = None,
        baudrate: int = 115200,
        unix_socket: Optional[str] = None,
        is_server: bool = False,
        log_file: Optional[Union[str, Path]] = None,
        timeout: float = 5.0,
    ):
        self.host = host
        self.port = port
        self.device = device
        self.baudrate = baudrate
        self.unix_socket = unix_socket
        self.is_server = is_server
        self.log_file = Path(log_file).resolve() if log_file else None
        self.timeout = timeout

        self.conn_socket: Optional[socket.socket] = None
        self.server_socket: Optional[socket.socket] = None
        self.serial_conn = None

        self._running = False
        self._rx_thread: Optional[threading.Thread] = None
        self._rx_buffer = bytearray()
        self._buffer_lock = threading.Lock()
        self._new_data_cond = threading.Condition(self._buffer_lock)
        self._log_handle = None
        self.callbacks: List[Callable[[bytes], None]] = []

    def connect(self, retry_count: int = 10, retry_delay: float = 0.5) -> None:
        """Establish connection to the UART stream."""
        if self.device:
            self._connect_serial()
        elif self.unix_socket:
            self._connect_unix(retry_count, retry_delay)
        elif self.is_server:
            self._listen_tcp()
        elif self.host and self.port:
            self._connect_tcp_client(retry_count, retry_delay)
        else:
            raise ValueError("No valid connection endpoint specified (device, unix_socket, or host/port).")

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self._log_handle = open(self.log_file, "ab")

        self._running = True
        self._rx_thread = threading.Thread(target=self._rx_worker, daemon=True)
        self._rx_thread.start()

    def _connect_tcp_client(self, retry_count: int, retry_delay: float) -> None:
        assert self.host is not None and self.port is not None
        last_err = None
        for i in range(retry_count):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(self.timeout)
                s.connect((self.host, self.port))
                self.conn_socket = s
                print(f"[UART] Connected to TCP socket {self.host}:{self.port}")
                return
            except (ConnectionRefusedError, socket.timeout, OSError) as e:
                last_err = e
                time.sleep(retry_delay)
        raise ConnectionError(f"Failed to connect to UART TCP server at {self.host}:{self.port}: {last_err}")

    def _listen_tcp(self) -> None:
        assert self.host is not None and self.port is not None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"[UART] Listening for QEMU/Target connection on {self.host}:{self.port}...")
        self.conn_socket, addr = self.server_socket.accept()
        print(f"[UART] Target connected from {addr[0]}:{addr[1]}")

    def _connect_unix(self, retry_count: int, retry_delay: float) -> None:
        assert self.unix_socket is not None
        last_err = None
        for i in range(retry_count):
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(self.timeout)
                s.connect(self.unix_socket)
                self.conn_socket = s
                print(f"[UART] Connected to UNIX domain socket: {self.unix_socket}")
                return
            except (FileNotFoundError, ConnectionRefusedError, OSError) as e:
                last_err = e
                time.sleep(retry_delay)
        raise ConnectionError(f"Failed to connect to UNIX socket {self.unix_socket}: {last_err}")

    def _connect_serial(self) -> None:
        if not HAS_PYSERIAL:
            raise ImportError(
                "pyserial is required to connect to hardware TTY / serial ports.\n"
                "Install it using: pip install pyserial"
            )
        assert self.device is not None
        print(f"[UART] Opening serial port {self.device} at {self.baudrate} baud...")
        self.serial_conn = serial.Serial(self.device, self.baudrate, timeout=self.timeout)

    def _rx_worker(self) -> None:
        """Background thread to read data from UART and distribute to buffer/callbacks."""
        while self._running:
            try:
                chunk = b""
                if self.conn_socket:
                    chunk = self.conn_socket.recv(4096)
                    if not chunk:
                        print("\n[UART] Remote connection closed.")
                        break
                elif self.serial_conn:
                    chunk = self.serial_conn.read(self.serial_conn.in_waiting or 1)
                    if not chunk:
                        time.sleep(0.01)
                        continue

                if chunk:
                    with self._new_data_cond:
                        self._rx_buffer.extend(chunk)
                        self._new_data_cond.notify_all()

                    if self._log_handle:
                        self._log_handle.write(chunk)
                        self._log_handle.flush()

                    for cb in self.callbacks:
                        try:
                            cb(chunk)
                        except Exception as e:
                            print(f"[UART Callback Error] {e}", file=sys.stderr)

            except socket.timeout:
                continue
            except (OSError, ConnectionResetError):
                break
            except Exception as e:
                if self._running:
                    print(f"[UART RX Error] {e}", file=sys.stderr)
                break

    def write(self, data: Union[str, bytes]) -> int:
        """Send raw data to UART."""
        raw = data.encode("utf-8") if isinstance(data, str) else data
        if self.conn_socket:
            return self.conn_socket.send(raw)
        elif self.serial_conn:
            return self.serial_conn.write(raw)
        else:
            raise RuntimeError("UART is not connected.")

    def write_line(self, line: str) -> int:
        """Send a string followed by newline to UART."""
        if not line.endswith("\n"):
            line += "\n"
        return self.write(line)

    def send_file(self, filepath: Union[str, Path], chunk_size: int = 512, delay: float = 0.005) -> int:
        """Stream a binary or text file to UART in chunks (useful for ML vectors or firmware data)."""
        path = Path(filepath).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        total_bytes = 0
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                self.write(chunk)
                total_bytes += len(chunk)
                if delay > 0:
                    time.sleep(delay)

        print(f"[UART] Streamed {total_bytes} bytes from {path.name}")
        return total_bytes

    def read_existing(self) -> bytes:
        """Retrieve all currently accumulated bytes from the RX buffer without waiting."""
        with self._buffer_lock:
            data = bytes(self._rx_buffer)
            self._rx_buffer.clear()
            return data

    def readline(self, timeout: Optional[float] = None) -> str:
        """Read a single newline-terminated line from UART."""
        end_time = time.time() + (timeout if timeout is not None else self.timeout)
        while True:
            with self._new_data_cond:
                newline_pos = self._rx_buffer.find(b"\n")
                if newline_pos != -1:
                    line_bytes = self._rx_buffer[: newline_pos + 1]
                    del self._rx_buffer[: newline_pos + 1]
                    return line_bytes.decode("utf-8", errors="replace")

                rem = end_time - time.time()
                if rem <= 0:
                    raise TimeoutError("UART readline() timed out.")
                self._new_data_cond.wait(timeout=min(rem, 0.2))

    def expect(self, pattern: str, timeout: float = 10.0) -> str:
        """Wait for a regex pattern to appear in UART output, returning the matched text."""
        regex = re.compile(pattern)
        end_time = time.time() + timeout

        accumulated = ""
        while True:
            with self._new_data_cond:
                text = self._rx_buffer.decode("utf-8", errors="replace")
                match = regex.search(text)
                if match:
                    end_idx = match.end()
                    raw_consumed = len(text[:end_idx].encode("utf-8", errors="replace"))
                    del self._rx_buffer[:raw_consumed]
                    return match.group(0)

                rem = end_time - time.time()
                if rem <= 0:
                    raise TimeoutError(f"UART expect('{pattern}') timed out after {timeout}s.")
                self._new_data_cond.wait(timeout=min(rem, 0.2))

    def close(self) -> None:
        """Disconnect and stop background receiver."""
        self._running = False
        if self.conn_socket:
            try:
                self.conn_socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.conn_socket.close()
            except Exception:
                pass
            self.conn_socket = None

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        if self.serial_conn:
            try:
                self.serial_conn.close()
            except Exception:
                pass
            self.serial_conn = None

        if self._log_handle:
            try:
                self._log_handle.close()
            except Exception:
                pass
            self._log_handle = None

        if self._rx_thread and self._rx_thread.is_alive():
            self._rx_thread.join(timeout=1.0)

    def __enter__(self) -> UartStreamer:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct argument parser for UART streamer with -h, --h, and --help support."""
    parser = argparse.ArgumentParser(
        description="MCUML UART Streamer (uart.py): Stream, log, and interact with UART from QEMU or Silicon.",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Connect to QEMU UART listening on TCP 127.0.0.1:5555:
  python3 tools/sim/uart.py --host 127.0.0.1 --port 5555

  # Host a TCP server and wait for QEMU to connect:
  python3 tools/sim/uart.py --server --port 5555

  # Connect to hardware serial or virtual PTY:
  python3 tools/sim/uart.py --device /dev/ttyUSB0 --baud 115200

  # Send a file (e.g. ML input tensor) and log output:
  python3 tools/sim/uart.py --port 5555 --send-file input_tensor.bin --log-file uart.log

  # Automated test: Wait for expected string with timeout:
  python3 tools/sim/uart.py --port 5555 --expect "INFERENCE SUCCESS" --timeout 15.0
""",
    )

    help_group = parser.add_argument_group("Help and Information")
    help_group.add_argument(
        "-h",
        "--h",
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit (accepts -h, --h, or --help).",
    )

    conn_group = parser.add_argument_group("Connection Options")
    conn_group.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Target host address for TCP connection (default: 127.0.0.1).",
    )
    conn_group.add_argument(
        "-p",
        "--port",
        type=int,
        default=5555,
        help="TCP port for UART stream (default: 5555).",
    )
    conn_group.add_argument(
        "--server",
        "--listen",
        dest="is_server",
        action="store_true",
        help="Run as TCP server and listen for incoming connection from QEMU/target.",
    )
    conn_group.add_argument(
        "-d",
        "--device",
        type=str,
        default=None,
        help="Hardware serial device or PTY (e.g. /dev/ttyUSB0 or /dev/pts/2).",
    )
    conn_group.add_argument(
        "-b",
        "--baud",
        dest="baudrate",
        type=int,
        default=115200,
        help="Serial baud rate (default: 115200).",
    )
    conn_group.add_argument(
        "--unix",
        dest="unix_socket",
        type=str,
        default=None,
        help="UNIX domain socket path (e.g. /tmp/uart.sock).",
    )

    action_group = parser.add_argument_group("Actions and Automation")
    action_group.add_argument(
        "--send",
        type=str,
        default=None,
        help="Send a string to the UART upon connection.",
    )
    action_group.add_argument(
        "--send-file",
        type=str,
        default=None,
        help="Stream a file (binary or text) over UART upon connection.",
    )
    action_group.add_argument(
        "--expect",
        type=str,
        default=None,
        help="Wait for a specific regex pattern in the UART stream and exit.",
    )
    action_group.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=10.0,
        help="Timeout in seconds for connection and expect operations (default: 10.0).",
    )
    action_group.add_argument(
        "-l",
        "--log-file",
        type=str,
        default=None,
        help="Mirror all UART stream data to specified log file.",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI Entry point for UART streamer."""
    if argv is None:
        argv = sys.argv[1:]

    if any(arg in ("--h", "-h", "--help") for arg in argv):
        parser = build_arg_parser()
        parser.print_help()
        return 0

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    streamer = UartStreamer(
        host=args.host,
        port=args.port,
        device=args.device,
        baudrate=args.baudrate,
        unix_socket=args.unix_socket,
        is_server=args.is_server,
        log_file=args.log_file,
        timeout=args.timeout,
    )

    # Echo incoming data to stdout in real-time
    def _print_incoming(data: bytes) -> None:
        sys.stdout.write(data.decode("utf-8", errors="replace"))
        sys.stdout.flush()

    streamer.callbacks.append(_print_incoming)

    try:
        streamer.connect()

        # Send initial command string if provided
        if args.send:
            streamer.write_line(args.send)

        # Stream file if provided
        if args.send_file:
            streamer.send_file(args.send_file)

        # Automated pattern matching
        if args.expect:
            print(f"[UART] Waiting up to {args.timeout}s for pattern: '{args.expect}'...")
            matched = streamer.expect(args.expect, timeout=args.timeout)
            print(f"\n[UART] Successfully matched: '{matched}'")
            return 0

        # Interactive streaming mode if no batch expect was given
        print("[UART] Streaming started. Press Ctrl+C to disconnect.\n---")
        while streamer._running:
            time.sleep(0.2)

        return 0

    except KeyboardInterrupt:
        print("\n[UART] Streaming stopped by user.")
        return 0
    except TimeoutError as e:
        print(f"\n[UART TIMEOUT] {e}", file=sys.stderr)
        return 124
    except Exception as e:
        print(f"\n[UART ERROR] {e}", file=sys.stderr)
        return 1
    finally:
        streamer.close()


if __name__ == "__main__":
    sys.exit(main())
