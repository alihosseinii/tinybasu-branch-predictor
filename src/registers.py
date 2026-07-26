"""
registers.py

Register File implementation for TinyBASU.
"""

from __future__ import annotations


class RegisterFile:
    """
    Represents the 8 general-purpose registers.
    """

    REGISTER_COUNT = 8

    def __init__(self) -> None:
        self._registers = [0] * self.REGISTER_COUNT

    # --------------------------------------------------
    # Register Operations
    # --------------------------------------------------

    def read(self, index: int) -> int:
        """
        Read the value of a register.
        """

        self._validate(index)
        return self._registers[index]

    def write(self, index: int, value: int) -> None:
        """
        Write a value into a register.
        """

        self._validate(index)
        self._registers[index] = value

    # --------------------------------------------------
    # Utility
    # --------------------------------------------------

    def reset(self) -> None:
        """
        Clear all registers.
        """

        self._registers = [0] * self.REGISTER_COUNT

    def dump(self) -> list[int]:
        """
        Return a copy of the register file.
        """

        return self._registers.copy()

    def __len__(self) -> int:
        return self.REGISTER_COUNT

    def __getitem__(self, index: int) -> int:
        return self.read(index)

    def __setitem__(self, index: int, value: int) -> None:
        self.write(index, value)

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def _validate(self, index: int) -> None:
        if not (0 <= index < self.REGISTER_COUNT):
            raise IndexError(
                f"Invalid register R{index}."
            )