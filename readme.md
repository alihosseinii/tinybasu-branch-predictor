# TinyBASU Processor Simulator and Branch Prediction Algorithms

Implementation of the final project for the Computer Architecture course (Branch Prediction in the TinyBASU Processor).

## Folder Structure

project/
├── asm/                    # Module 1: Assembly codes
│   ├── fibo_bne.asm        #   30th Fibonacci with bne (fixed from appendix 1)
│   ├── fibo_beq.asm        #   30th Fibonacci with beq (fixed from appendix 2)
│   └── fact.asm            #   Factorial of 50 (multiplication via repeated addition - nested loop)
├── data/
│   └── empty.txt           # Empty data file (programs don't use data memory)
├── src/                    # Modules 2 and 3: Simulator
│   ├── assembler.py        #   Assembler (assembly text -> 16-bit machine code)
│   ├── simulator.py        #   Simulator core + 5 branch prediction algorithms
│   ├── main.py             #   Command-line entry point
│   └── run_module4.py      #   Automated execution of all combinations (Module 4)
└── reports/                # Module 4: 15 report file outputs

## How to Run

```bash
cd src
python main.py <timeout_cycles> <prediction_method> <inst_file> <data_file> <report_file>

# prediction_method: ST, SN, D1, D2, IQ
# Example:
python main.py 100000 D2 ../asm/fibo_bne.asm ../data/empty.txt report.txt
```

To generate all 15 requested reports from Module 4 at once:

```bash
cd src
python run_module4.py
```

## Implemented Architecture

- 8 16-bit registers (rx0..rx7), no register is hardwired to zero.
- 512-word memory: addresses 0..255 for instructions, 256..511 for data.
- Three instruction formats R/I/J according to Figure 2 of the project document.
- Branch/jump offset is calculated relative to the instruction's own address:
  `PC_new = PC_instruction + imm` (if taken) or `PC_instruction + 1`.
- Branch Penalty = 3 cycles, according to the document (5-stage pipeline).
- Cycle model: each base instruction consumes 1 cycle; for each incorrect
  prediction on conditional branches (beq/bne) or each unconditional jump
  instruction (jmp/jal) whose destination is not known at fetch/decode,
  3 penalty cycles (pipeline flush) are added.

## Branch Prediction Algorithms (Module 3)

| Code | Name | Description |
|------|------|-------------|
| ST | Static Taken | Always predicts "taken" |
| SN | Static Not Taken | Always predicts "not taken" |
| D1 | Dynamic 1-bit | Two-state state machine (top of Figure 1 in the document) |
| D2 | Dynamic 2-bit | Four-state saturating state machine (bottom of Figure 1 in the document) |
| IQ | Heuristic | 3-bit saturating counter (8 states) with weakly-taken initial value; deeper hysteresis than D2 for less oscillation against mispredictions (e.g., loop exit) |

All five algorithms maintain a table keyed by the branch instruction's PC address
(except ST/SN which are static and don't need a table).

## Verification Notes

- Output of `fibo_bne.asm` and `fibo_beq.asm` is independent of the prediction
  algorithm, always identical (rx4 = 45608); because prediction only affects
  *performance* (cycle count), not *correctness* of the computational result.
- Output of `fact.asm` (rx1 = 0) matches `math.factorial(50) % 65536` in Python
  (natural overflow in 16-bit registers).
