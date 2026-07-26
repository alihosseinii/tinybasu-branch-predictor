"""
parser.py

Parser for TinyBASU assembly and data files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from instruction import Instruction


class Parser:
    """
    Parses TinyBASU assembly programs and data files.
    """

    def __init__(self) -> None:
        self.labels: Dict[str, int] = {}

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def parse_program(self, filename: str) -> list[Instruction]:
        """
        Parse an assembly program.
        """

        self.labels.clear()

        lines = self._read_lines(filename)

        self._collect_labels(lines)

        return self._build_program(lines)

    def parse_data(self, filename: str) -> list[int]:
        """
        Parse a data file.
        """

        lines = self._read_lines(filename)

        data: list[int] = []

        for line in lines:

            line = self._clean_line(line)

            if not line:
                continue

            data.append(int(line))

        return data

    # -------------------------------------------------
    # First Pass
    # -------------------------------------------------

    def _collect_labels(
        self,
        lines: list[str],
    ) -> None:
        """
        First pass.
        Collect labels.
        """

        address = 0

        for line in lines:

            line = self._clean_line(line)

            if not line:
                continue

            if ":" in line:

                label = line.split(":")[0].strip()

                self.labels[label] = address

                if line.endswith(":"):
                    continue

            address += 1

    # -------------------------------------------------
    # Second Pass
    # -------------------------------------------------

    def _build_program(
        self,
        lines: list[str],
    ) -> list[Instruction]:
        """
        Second pass.
        Create Instruction objects.
        """

        program: list[Instruction] = []

        address = 0

        for line in lines:

            original = line

            line = self._clean_line(line)

            if not line:
                continue

            if ":" in line:

                parts = line.split(":", 1)

                line = parts[1].strip()

                if not line:
                    continue

            instruction = self._parse_instruction(
                line,
                address,
                original.rstrip(),
            )

            program.append(instruction)

            address += 1

        return program

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def _parse_instruction(
        self,
        line: str,
        address: int,
        raw_text: str,
    ) -> Instruction:
        """
        Parse one assembly instruction.

        Actual instruction decoding
        will be implemented later.
        """

        parts = line.replace(",", " ").split()

        opcode = parts[0].upper()

        return Instruction(
            opcode=opcode,
            address=address,
            raw_text=raw_text,
        )

    @staticmethod
    def _read_lines(filename: str) -> list[str]:

        return Path(filename).read_text(
            encoding="utf-8"
        ).splitlines()

    @staticmethod
    def _clean_line(line: str) -> str:

        line = line.split("#")[0]

        return line.strip()