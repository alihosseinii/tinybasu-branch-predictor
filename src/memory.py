"""
memory.py

Memory model for the TinyBASU simulator.

Memory layout:

0   - 255   : Instructions
256 - 511   : Data
"""

from __future__ import annotations

from typing import Optional

from instruction import Instruction


class Memory:
    """Represents the TinyBASU main memory."""

    MEMORY_SIZE = 512

    INSTRUCTION_START = 0
    INSTRUCTION_END = 255

    DATA_START = 256
    DATA_END = 511

    def __init__(self) -> None:
        self._cells: list[Optional[Instruction | int]] = [
            None
        ] * self.MEMORY_SIZE

    # --------------------------------------------------
    # Instruction Section
    # --------------------------------------------------

    def load_program(self, program: list[Instruction]) -> None:
        """
        Load instructions into memory starting from address 0.
        """

        if len(program) > 256:
            raise ValueError("Program is larger than instruction memory.")

        for address, instruction in enumerate(program):
            instruction.address = address
            self._cells[address] = instruction

    def fetch_instruction(self, address: int) -> Instruction:
        """
        Returns the instruction stored at the given address.
        """

        self._validate_instruction_address(address)

        instruction = self._cells[address]

        if not isinstance(instruction, Instruction):
            raise TypeError(
                f"No instruction found at address {address}."
            )

        return instruction

    # --------------------------------------------------
    # Data Section
    # --------------------------------------------------

    def load_data(self, data: list[int]) -> None:
        """
        Loads the data segment into memory.
        """

        if len(data) > 256:
            raise ValueError("Data segment is too large.")

        start = self.DATA_START

        for offset, value in enumerate(data):
            self._cells[start + offset] = value

    def read_data(self, address: int) -> int:
        """
        Reads one integer from the data memory.
        """

        self._validate_data_address(address)

        value = self._cells[address]

        if value is None:
            return 0

        if isinstance(value, Instruction):
            raise TypeError(
                "Instruction found inside data segment."
            )

        return value

    def write_data(self, address: int, value: int) -> None:
        """
        Writes one integer into data memory.
        """

        self._validate_data_address(address)

        self._cells[address] = value

    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    def clear(self) -> None:
        """Clears the entire memory."""

        self._cells = [None] * self.MEMORY_SIZE

    def dump(self) -> list[Optional[Instruction | int]]:
        """
        Returns a copy of the entire memory.
        """

        return self._cells.copy()

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def _validate_instruction_address(self, address: int) -> None:
        if not (
            self.INSTRUCTION_START
            <= address
            <= self.INSTRUCTION_END
        ):
            raise ValueError(
                f"{address} is outside instruction memory."
            )

    def _validate_data_address(self, address: int) -> None:
        if not (
            self.DATA_START
            <= address
            <= self.DATA_END
        ):
            raise ValueError(
                f"{address} is outside data memory."
            )