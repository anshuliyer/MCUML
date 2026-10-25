#!/usr/bin/env python3
"""MCUML Simulation Connector (sim_connect.py).

QEMU Python Wrapper for ARM Cortex-M33 Simulation.

Features:
- Launches and manages QEMU simulation targeting Cortex-M33 core.
- Accepts firmware/kernel binaries via --kernel / -kernel.
- Exposes all native QEMU flags (passthrough of any extra flags).
- Supports -h, --h, and --help for command-line help.
- Provides interactive terminal, GDB debug server, QEMU monitor, and QMP connections.
- Callable both as a standalone CLI tool and as an importable Python library.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


class QemuSimulator:
    """Wrapper and manager for QEMU Cortex-M33 simulation instances."""

    DEFAULT_MACHINE = "mps2-an505"
    DEFAULT_CPU = "cortex-m33"
    DEFAULT_SERIAL = "mon:stdio"
    DEFAULT_GDB_PORT = 1234

    def __init__(
        self,
        kernel: Optional[Union[str, Path]] = None,
        machine: str = DEFAULT_MACHINE,
        cpu: str = DEFAULT_CPU,
        memory: Optional[str] = None,
        nographic: bool = True,
        serial: str = DEFAULT_SERIAL,
        semihosting: bool = False,
        gdb_port: Optional[int] = None,
        wait_gdb: bool = False,
        monitor: Optional[str] = None,
        qmp: Optional[str] = None,
        timeout: Optional[float] = None,
        log_file: Optional[Union[str, Path]] = None,
        qemu_bin: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
    ):
        self.kernel = Path(kernel).resolve() if kernel else None
        self.machine = machine
        self.cpu = cpu
        self.memory = memory
        self.nographic = nographic
        self.serial = serial
        self.semihosting = semihosting
        self.gdb_port = gdb_port
        self.wait_gdb = wait_gdb
        self.monitor = monitor
        self.qmp = qmp
        self.timeout = timeout
        self.log_file = Path(log_file).resolve() if log_file else None
        self.extra_args = list(extra_args) if extra_args else []
        self.qemu_bin = self._find_qemu_binary(qemu_bin)
        self.process: Optional[subprocess.Popen] = None
        self._log_handle = None

    @staticmethod
    def _find_qemu_binary(custom_path: Optional[str] = None) -> str:
        """Find the qemu-system-arm binary on the host system."""
        if custom_path:
            resolved = shutil.which(custom_path) or custom_path
            if os.path.exists(resolved) and os.access(resolved, os.X_OK):
                return resolved
            raise FileNotFoundError(f"Specified QEMU binary not found or not executable: {custom_path}")

        env_bin = os.environ.get("QEMU_ARM_BIN")
        if env_bin:
            resolved = shutil.which(env_bin) or env_bin
            if os.path.exists(resolved) and os.access(resolved, os.X_OK):
                return resolved

        which_bin = shutil.which("qemu-system-arm")
        if which_bin:
            return which_bin

        candidate_paths = [
            "/usr/bin/qemu-system-arm",
            "/usr/local/bin/qemu-system-arm",
            "/opt/homebrew/bin/qemu-system-arm",
            "/usr/lib/qemu/qemu-system-arm",
        ]
        for candidate in candidate_paths:
            if os.path.exists(candidate) and os.access(candidate, os.X_OK):
                return candidate

        raise FileNotFoundError(
            "Could not locate 'qemu-system-arm'. Please install QEMU or specify the path via "
            "--qemu-bin or the QEMU_ARM_BIN environment variable.\n"
            "On Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y qemu-system-arm\n"
            "On macOS: brew install qemu"
        )

    def build_command(self) -> List[str]:
        """Build the full QEMU execution command list."""
        cmd = [self.qemu_bin]

        # Machine configuration
        if not any(arg in self.extra_args for arg in ("-M", "-machine", "--machine")):
            cmd.extend(["-machine", self.machine])

        # CPU configuration
        if not any(arg in self.extra_args for arg in ("-cpu", "--cpu")):
            cmd.extend(["-cpu", self.cpu])

        # Memory configuration
        if self.memory and not any(arg in self.extra_args for arg in ("-m", "--memory", "-memory")):
            cmd.extend(["-m", self.memory])

        # Kernel/Firmware binary
        if self.kernel:
            if not self.kernel.exists():
                raise FileNotFoundError(f"Kernel binary file does not exist: {self.kernel}")
            if not any(arg in self.extra_args for arg in ("-kernel", "--kernel")):
                cmd.extend(["-kernel", str(self.kernel)])

        # Display / Graphics
        if self.nographic and "-nographic" not in self.extra_args:
            cmd.append("-nographic")

        # Serial console
        if self.serial and not any(arg in self.extra_args for arg in ("-serial", "--serial")):
            cmd.extend(["-serial", self.serial])

        # Semihosting
        if self.semihosting and not any(arg in self.extra_args for arg in ("-semihosting", "--semihosting")):
            cmd.append("-semihosting")

        # GDB Server
        if self.gdb_port is not None:
            if "-s" not in self.extra_args and "-gdb" not in self.extra_args:
                if self.gdb_port == self.DEFAULT_GDB_PORT:
                    cmd.append("-s")
                else:
                    cmd.extend(["-gdb", f"tcp::{self.gdb_port}"])

        # Wait for GDB to connect
        if self.wait_gdb and "-S" not in self.extra_args:
            cmd.append("-S")

        # Monitor port
        if self.monitor and not any(arg in self.extra_args for arg in ("-monitor", "--monitor")):
            cmd.extend(["-monitor", self.monitor])

        # QMP Socket
        if self.qmp and not any(arg in self.extra_args for arg in ("-qmp", "--qmp")):
            cmd.extend(["-qmp", self.qmp])

        # Append any arbitrary extra QEMU arguments passed by user
        cmd.extend(self.extra_args)

        return cmd

    def start(self, capture_output: bool = False) -> subprocess.Popen:
        """Start the QEMU simulation process."""
        if self.process and self.process.poll() is None:
            raise RuntimeError("QEMU simulation process is already running.")

        cmd = self.build_command()
        print(f"[SIM-CONNECT] Starting QEMU command:\n  {' '.join(shlex.quote(c) for c in cmd)}\n")

        if self.gdb_port is not None:
            print(f"[SIM-CONNECT] GDB server active on port {self.gdb_port}.")
            if self.wait_gdb:
                print("[SIM-CONNECT] CPU paused at startup (-S). Connect GDB to resume:")
                kernel_str = str(self.kernel) if self.kernel else "<binary>"
                print(f"              arm-none-eabi-gdb -ex \"target remote localhost:{self.gdb_port}\" {kernel_str}")

        if self.monitor:
            print(f"[SIM-CONNECT] Monitor available at: {self.monitor}")

        if self.qmp:
            print(f"[SIM-CONNECT] QMP socket available at: {self.qmp}")

        stdin_stream = None if not capture_output else subprocess.PIPE
        stdout_stream = None if not capture_output else subprocess.PIPE
        stderr_stream = None if not capture_output else subprocess.STDOUT

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self._log_handle = open(self.log_file, "w", encoding="utf-8")
            if not capture_output:
                stdout_stream = subprocess.PIPE
                stderr_stream = subprocess.STDOUT

        self.process = subprocess.Popen(
            cmd,
            stdin=stdin_stream,
            stdout=stdout_stream,
            stderr=stderr_stream,
            text=True,
            bufsize=1,
        )

        if self.log_file and not capture_output and self.process.stdout:
            def _tee_output():
                try:
                    for line in iter(self.process.stdout.readline, ""):
                        sys.stdout.write(line)
                        sys.stdout.flush()
                        if self._log_handle:
                            self._log_handle.write(line)
                            self._log_handle.flush()
                except Exception:
                    pass

            t = threading.Thread(target=_tee_output, daemon=True)
            t.start()

        return self.process

    def wait(self, timeout: Optional[float] = None) -> int:
        """Wait for simulation to complete."""
        effective_timeout = timeout if timeout is not None else self.timeout
        if not self.process:
            raise RuntimeError("Simulation has not been started.")

        try:
            return self.process.wait(timeout=effective_timeout)
        except subprocess.TimeoutExpired:
            print(f"\n[SIM-CONNECT] Simulation timed out after {effective_timeout}s. Terminating QEMU...")
            self.stop()
            raise

    def stop(self, grace_period: float = 2.0) -> None:
        """Stop the running QEMU simulation."""
        if not self.process or self.process.poll() is not None:
            return

        try:
            self.process.send_signal(signal.SIGINT)
            self.process.wait(timeout=grace_period)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                self.process.terminate()
                self.process.wait(timeout=grace_period)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                self.process.kill()

        if self._log_handle:
            try:
                self._log_handle.close()
            except Exception:
                pass
            self._log_handle = None

    def is_running(self) -> bool:
        """Check if QEMU simulation is currently active."""
        return self.process is not None and self.process.poll() is None

    @staticmethod
    def connect_monitor(host: str = "127.0.0.1", port: int = 4444, timeout: float = 5.0) -> MonitorClient:
        """Connect to QEMU monitor via TCP telnet socket."""
        return MonitorClient(host=host, port=port, timeout=timeout)


class MonitorClient:
    """Helper client to connect to QEMU monitor socket."""

    def __init__(self, host: str = "127.0.0.1", port: int = 4444, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None

    def connect(self) -> None:
        """Establish connection to the QEMU monitor."""
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        time.sleep(0.1)
        self._read_available()

    def _read_available(self) -> str:
        if not self.sock:
            return ""
        self.sock.settimeout(0.2)
        chunks = []
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                chunks.append(data.decode("utf-8", errors="replace"))
            except socket.timeout:
                break
        self.sock.settimeout(self.timeout)
        return "".join(chunks)

    def execute(self, command: str) -> str:
        """Send a monitor command (e.g. 'info registers', 'system_reset') and return output."""
        if not self.sock:
            self.connect()
        assert self.sock is not None
        cmd_bytes = (command.strip() + "\n").encode("utf-8")
        self.sock.sendall(cmd_bytes)
        time.sleep(0.1)
        return self._read_available()

    def close(self) -> None:
        """Close monitor connection."""
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def __enter__(self) -> MonitorClient:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def print_qemu_native_help(qemu_bin: Optional[str] = None) -> int:
    """Print native QEMU help flags directly from qemu-system-arm."""
    try:
        bin_path = QemuSimulator._find_qemu_binary(qemu_bin)
        print(f"=== QEMU Native Help ({bin_path}) ===\n")
        res = subprocess.run([bin_path, "-help"], stdout=sys.stdout, stderr=sys.stderr)
        return res.returncode
    except Exception as e:
        print(f"Error fetching QEMU help: {e}", file=sys.stderr)
        return 1


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct argument parser with -h, --h, and --help support."""
    parser = argparse.ArgumentParser(
        description="MCUML Simulation Connector (sim_connect.py): Connect to QEMU, simulate Cortex-M33 core, and run firmware binaries.",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic run of Cortex-M33 firmware binary:
  python3 tools/sim/sim_connect.py --kernel path/to/firmware.elf

  # Run with GDB server enabled (port 1234) and wait for GDB connection:
  python3 tools/sim/sim_connect.py --kernel firmware.elf -s -S

  # Expose QEMU monitor on telnet port 4444:
  python3 tools/sim/sim_connect.py --kernel firmware.elf --monitor telnet:127.0.0.1:4444,server,nowait

  # Passthrough arbitrary QEMU flags:
  python3 tools/sim/sim_connect.py --kernel firmware.elf -d in_asm,int -D /tmp/qemu.log

  # Show native QEMU help:
  python3 tools/sim/sim_connect.py --qemu-help
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
    help_group.add_argument(
        "--qemu-help",
        action="store_true",
        help="Print full native help options from qemu-system-arm.",
    )

    core_group = parser.add_argument_group("Simulation Configuration")
    core_group.add_argument(
        "-k",
        "--kernel",
        "-kernel",
        dest="kernel",
        type=str,
        default=None,
        help="Path to kernel/firmware binary (ELF or raw binary) to flash and run on Cortex-M33.",
    )
    core_group.add_argument(
        "-M",
        "--machine",
        "-machine",
        dest="machine",
        type=str,
        default=QemuSimulator.DEFAULT_MACHINE,
        help=f"QEMU machine model (default: {QemuSimulator.DEFAULT_MACHINE}).",
    )
    core_group.add_argument(
        "--cpu",
        "-cpu",
        dest="cpu",
        type=str,
        default=QemuSimulator.DEFAULT_CPU,
        help=f"Target CPU core (default: {QemuSimulator.DEFAULT_CPU}).",
    )
    core_group.add_argument(
        "-m",
        "--memory",
        "-memory",
        dest="memory",
        type=str,
        default=None,
        help="RAM size (e.g. 16M, 32M). Defaults to board specification.",
    )
    core_group.add_argument(
        "--semihosting",
        "-semihosting",
        dest="semihosting",
        action="store_true",
        help="Enable ARM semihosting for stdout/debugging.",
    )
    core_group.add_argument(
        "--serial",
        "-serial",
        dest="serial",
        type=str,
        default=QemuSimulator.DEFAULT_SERIAL,
        help=f"Serial port device configuration (default: {QemuSimulator.DEFAULT_SERIAL}).",
    )
    core_group.add_argument(
        "--graphic",
        dest="nographic",
        action="store_false",
        help="Enable graphic window display (defaults to nographic mode).",
    )

    debug_group = parser.add_argument_group("Debugging and Monitoring")
    debug_group.add_argument(
        "-s",
        "--gdb",
        dest="gdb_port",
        nargs="?",
        const=QemuSimulator.DEFAULT_GDB_PORT,
        type=int,
        default=None,
        help=f"Start GDB server (default port: {QemuSimulator.DEFAULT_GDB_PORT} or specify port number).",
    )
    debug_group.add_argument(
        "-S",
        "--wait-gdb",
        dest="wait_gdb",
        action="store_true",
        help="Freeze CPU execution at startup and wait for GDB connection before running.",
    )
    debug_group.add_argument(
        "--monitor",
        "-monitor",
        dest="monitor",
        type=str,
        default=None,
        help="Configure QEMU monitor (e.g. 'telnet:127.0.0.1:4444,server,nowait' or 'stdio').",
    )
    debug_group.add_argument(
        "--qmp",
        "-qmp",
        dest="qmp",
        type=str,
        default=None,
        help="Configure QMP socket (e.g. 'tcp:127.0.0.1:4445,server,nowait').",
    )

    execution_group = parser.add_argument_group("Execution Controls")
    execution_group.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Simulation run timeout in seconds (auto-terminate).",
    )
    execution_group.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to file for logging simulation output.",
    )
    execution_group.add_argument(
        "--qemu-bin",
        type=str,
        default=None,
        help="Path to custom qemu-system-arm executable.",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI Entry point."""
    if argv is None:
        argv = sys.argv[1:]

    # Explicitly check for --h, -h, or --help first if present in argv
    if any(arg in ("--h", "-h", "--help") for arg in argv):
        parser = build_arg_parser()
        parser.print_help()
        return 0

    parser = build_arg_parser()
    args, unknown_args = parser.parse_known_args(argv)

    if args.qemu_help:
        return print_qemu_native_help(args.qemu_bin)

    if not args.kernel and "-kernel" not in unknown_args and "--kernel" not in unknown_args:
        parser.print_help()
        print("\n[ERROR] Missing required argument: --kernel <binary_path>", file=sys.stderr)
        return 2

    passthrough_args = [arg for arg in unknown_args if arg != "--"]

    sim = QemuSimulator(
        kernel=args.kernel,
        machine=args.machine,
        cpu=args.cpu,
        memory=args.memory,
        nographic=args.nographic,
        serial=args.serial,
        semihosting=args.semihosting,
        gdb_port=args.gdb_port,
        wait_gdb=args.wait_gdb,
        monitor=args.monitor,
        qmp=args.qmp,
        timeout=args.timeout,
        log_file=args.log_file,
        qemu_bin=args.qemu_bin,
        extra_args=passthrough_args,
    )

    def _sig_handler(signum, frame):
        print("\n[SIM-CONNECT] Interrupt received. Shutting down QEMU...")
        sim.stop()
        sys.exit(130)

    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    try:
        sim.start()
        exit_code = sim.wait()
        return exit_code
    except subprocess.TimeoutExpired:
        return 124
    except Exception as e:
        print(f"[SIM-CONNECT ERROR] {e}", file=sys.stderr)
        return 1
    finally:
        sim.stop()


if __name__ == "__main__":
    sys.exit(main())
