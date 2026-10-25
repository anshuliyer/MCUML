#!/usr/bin/env python3
"""MCUML GDB Debug Module (debug.py).

Connects to QEMU Cortex-M33 GDB stub or hardware debug servers.

Features:
- Auto-detects ARM GDB binaries (arm-none-eabi-gdb, gdb-multiarch, gdb).
- Interactive GDB console with automatic target remote connection and ELF loading.
- Non-interactive batch mode for automated testing, assertions, and verification.
- Quick inspection helpers: read registers, read memory, set breakpoints, backtraces.
- Supports -h, --h, and --help for CLI help.
- Importable Python class (GdbSession) for scripting and test automation.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


class GdbSession:
    """Manages a GDB connection to QEMU or hardware debug targets."""

    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 1234

    def __init__(
        self,
        elf: Optional[Union[str, Path]] = None,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        gdb_bin: Optional[str] = None,
        timeout: float = 15.0,
    ):
        self.elf = Path(elf).resolve() if elf else None
        self.host = host
        self.port = port
        self.timeout = timeout
        self.gdb_bin = self._find_gdb_binary(gdb_bin)
        self.process: Optional[subprocess.Popen] = None

    @staticmethod
    def _find_gdb_binary(custom_path: Optional[str] = None) -> str:
        """Find an ARM-compatible GDB executable on the system."""
        if custom_path:
            resolved = shutil.which(custom_path) or custom_path
            if os.path.exists(resolved) and os.access(resolved, os.X_OK):
                return resolved
            raise FileNotFoundError(f"Specified GDB binary not found or not executable: {custom_path}")

        env_bin = os.environ.get("ARM_GDB_BIN")
        if env_bin:
            resolved = shutil.which(env_bin) or env_bin
            if os.path.exists(resolved) and os.access(resolved, os.X_OK):
                return resolved

        candidates = [
            "arm-none-eabi-gdb",
            "gdb-multiarch",
            "/opt/homebrew/bin/arm-none-eabi-gdb",
            "/usr/bin/arm-none-eabi-gdb",
            "/usr/bin/gdb-multiarch",
            "gdb",
        ]
        for candidate in candidates:
            resolved = shutil.which(candidate)
            if resolved and os.access(resolved, os.X_OK):
                return resolved

        raise FileNotFoundError(
            "Could not locate an ARM-compatible GDB binary (arm-none-eabi-gdb or gdb-multiarch).\n"
            "Please install it:\n"
            "  On Ubuntu/Debian: sudo apt-get install -y gdb-multiarch\n"
            "  On macOS: brew install arm-none-eabi-gdb"
        )

    def build_startup_commands(
        self,
        extra_commands: Optional[List[str]] = None,
        batch: bool = False,
    ) -> List[str]:
        """Construct the list of initialization commands for GDB."""
        cmds = [
            "set pagination off",
            "set confirm off",
        ]

        if self.elf and self.elf.is_file():
            cmds.append(f"file {self.elf}")

        cmds.append(f"target remote {self.host}:{self.port}")

        if extra_commands:
            cmds.extend(extra_commands)

        if batch:
            cmds.append("quit")

        return cmds

    def run_interactive(self, tui: bool = False, extra_commands: Optional[List[str]] = None) -> int:
        """Launch an interactive GDB session in the current terminal."""
        cmd = [self.gdb_bin, "-q"]
        if tui:
            cmd.append("-tui")

        init_cmds = self.build_startup_commands(extra_commands=extra_commands, batch=False)
        for c in init_cmds:
            cmd.extend(["-ex", c])

        print(f"[GDB] Launching interactive session:\n  {' '.join(shlex.quote(c) for c in cmd)}\n")
        res = subprocess.run(cmd)
        return res.returncode

    def run_batch(self, commands: List[str]) -> Tuple[int, str]:
        """Run GDB non-interactively with a series of commands and return (exit_code, output)."""
        cmd = [self.gdb_bin, "-q", "--batch"]
        init_cmds = self.build_startup_commands(extra_commands=commands, batch=True)
        for c in init_cmds:
            cmd.extend(["-ex", c])

        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=self.timeout,
        )
        return res.returncode, res.stdout

    def read_registers(self) -> Dict[str, str]:
        """Read and parse general-purpose and special ARM Cortex-M registers."""
        code, out = self.run_batch(["info registers"])
        registers = {}
        for line in out.splitlines():
            line = line.strip()
            # Match standard GDB output format: 'r0   0x0   0'
            parts = line.split()
            if len(parts) >= 2:
                reg_name = parts[0]
                reg_val = parts[1]
                registers[reg_name] = reg_val
        return registers

    def read_memory(self, address: Union[int, str], num_words: int = 16) -> str:
        """Inspect memory contents in hexadecimal format at given address."""
        addr_str = hex(address) if isinstance(address, int) else address
        code, out = self.run_batch([f"x/{num_words}xw {addr_str}"])
        return out


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct argument parser for GDB debug module with -h, --h, and --help support."""
    parser = argparse.ArgumentParser(
        description="MCUML GDB Debugger (debug.py): Connect to QEMU Cortex-M33 GDB stub or hardware debug target.",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch interactive GDB connected to QEMU on port 1234:
  python3 tools/sim/debug.py --elf path/to/firmware.elf

  # Connect to custom host/port with TUI enabled:
  python3 tools/sim/debug.py --elf firmware.elf --port 1234 --tui

  # Read Cortex-M33 registers non-interactively and exit:
  python3 tools/sim/debug.py --elf firmware.elf --read-regs

  # Read memory region in hex (e.g. SRAM at 0x20000000, 32 words):
  python3 tools/sim/debug.py --read-mem 0x20000000 32

  # Run custom commands in batch mode:
  python3 tools/sim/debug.py --elf firmware.elf --batch -c "b main; continue; info registers"
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

    target_group = parser.add_argument_group("Target and Symbols")
    target_group.add_argument(
        "-e",
        "--elf",
        type=str,
        default=None,
        help="Path to firmware ELF file with symbols.",
    )
    target_group.add_argument(
        "--host",
        type=str,
        default=GdbSession.DEFAULT_HOST,
        help=f"GDB server host (default: {GdbSession.DEFAULT_HOST}).",
    )
    target_group.add_argument(
        "-p",
        "--port",
        type=int,
        default=GdbSession.DEFAULT_PORT,
        help=f"GDB server port (default: {GdbSession.DEFAULT_PORT}).",
    )
    target_group.add_argument(
        "--gdb-bin",
        type=str,
        default=None,
        help="Path to custom arm-none-eabi-gdb or gdb-multiarch binary.",
    )

    mode_group = parser.add_argument_group("Execution Modes")
    mode_group.add_argument(
        "--tui",
        action="store_true",
        help="Launch GDB in Text User Interface (TUI) mode.",
    )
    mode_group.add_argument(
        "--batch",
        action="store_true",
        help="Execute commands non-interactively in batch mode and exit.",
    )
    mode_group.add_argument(
        "-c",
        "--command",
        dest="commands",
        type=str,
        default=None,
        help="Semicolon-separated list of GDB commands to execute.",
    )
    mode_group.add_argument(
        "--break",
        dest="breakpoint",
        type=str,
        default=None,
        help="Set breakpoint at function name or address before starting.",
    )

    inspect_group = parser.add_argument_group("Inspection Utilities")
    inspect_group.add_argument(
        "--read-regs",
        action="store_true",
        help="Inspect and print all Cortex-M core registers, then exit.",
    )
    inspect_group.add_argument(
        "--read-mem",
        nargs=2,
        metavar=("ADDR", "WORDS"),
        help="Dump memory at ADDR for WORDS 32-bit words (e.g. --read-mem 0x20000000 16).",
    )
    inspect_group.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=15.0,
        help="Command timeout for batch operations in seconds (default: 15.0).",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI Entry point for GDB debug module."""
    if argv is None:
        argv = sys.argv[1:]

    if any(arg in ("--h", "-h", "--help") for arg in argv):
        parser = build_arg_parser()
        parser.print_help()
        return 0

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        session = GdbSession(
            elf=args.elf,
            host=args.host,
            port=args.port,
            gdb_bin=args.gdb_bin,
            timeout=args.timeout,
        )
    except FileNotFoundError as e:
        print(f"[GDB ERROR] {e}", file=sys.stderr)
        return 1

    extra_cmds: List[str] = []
    if args.breakpoint:
        extra_cmds.append(f"break {args.breakpoint}")
    if args.commands:
        extra_cmds.extend([c.strip() for c in args.commands.split(";") if c.strip()])

    # Inspect registers utility
    if args.read_regs:
        print(f"[GDB] Fetching core registers from {args.host}:{args.port}...")
        try:
            regs = session.read_registers()
            if not regs:
                print("[GDB] No registers returned (is QEMU running and paused?).")
                return 1
            print("\n=== Cortex-M Core Registers ===")
            for name, val in sorted(regs.items()):
                print(f"  {name:<10}: {val}")
            return 0
        except Exception as e:
            print(f"[GDB ERROR] {e}", file=sys.stderr)
            return 1

    # Inspect memory utility
    if args.read_mem:
        addr, words = args.read_mem
        print(f"[GDB] Dumping {words} words from memory address {addr}...")
        try:
            out = session.read_memory(address=addr, num_words=int(words))
            print(out)
            return 0
        except Exception as e:
            print(f"[GDB ERROR] {e}", file=sys.stderr)
            return 1

    # Batch command execution
    if args.batch:
        try:
            code, out = session.run_batch(commands=extra_cmds)
            print(out)
            return code
        except Exception as e:
            print(f"[GDB ERROR] {e}", file=sys.stderr)
            return 1

    # Default: Interactive GDB console
    try:
        return session.run_interactive(tui=args.tui, extra_commands=extra_cmds)
    except Exception as e:
        print(f"[GDB ERROR] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
