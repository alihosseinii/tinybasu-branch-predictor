"""
instruction.py

Defines the Instruction class used by the TinyBASU simulator.
Each assembly instruction is parsed once and stored as an
Instruction object before execution.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Instruction:
    """
    Represents a single TinyBASU instruction.
    """

    opcode: str

    rd: Optional[int] = None
    rs: Optional[int] = None
    rt: Optional[int] = None

    immediate: Optional[int] = None
    target: Optional[int] = None

    address: int = 0

    raw_text: str = ""

    def __repr__(self) -> str:
        return (
            f"Instruction("
            f"opcode={self.opcode}, "
            f"rd={self.rd}, "
            f"rs={self.rs}, "
            f"rt={self.rt}, "
            f"imm={self.immediate}, "
            f"target={self.target}, "
            f"addr={self.address})"
        )

    def __str__(self) -> str:
        return self.raw_text if self.raw_text else self.__repr__()