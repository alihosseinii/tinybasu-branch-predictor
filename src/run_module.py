import os
import time
import sys

sys.path.insert(0, os.path.dirname(__file__))
from simulator import TinyBASUSimulator

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASM_DIR = os.path.join(BASE, 'asm')
DATA_FILE = os.path.join(BASE, 'data', 'empty.txt')
REPORT_DIR = os.path.join(BASE, 'reports')

TIMEOUT_CYCLES = 200000

PROGRAMS = {
    'fibo_beq': 'fibo_beq.asm',
    'fibo_bne': 'fibo_bne.asm',
    'fact': 'fact.asm',
}

METHODS = ['ST', 'SN', 'D1', 'D2', 'IQ']


def main():
    os.makedirs(REPORT_DIR, exist_ok=True)
    summary = []
    for prog_key, asm_name in PROGRAMS.items():
        inst_file = os.path.join(ASM_DIR, asm_name)
        for method in METHODS:
            report_name = f"{prog_key}_{method.lower()}.txt"
            report_path = os.path.join(REPORT_DIR, report_name)

            sim = TinyBASUSimulator(method)
            start = time.perf_counter()
            sim.parse_instruction(inst_file)
            sim.init_memory(DATA_FILE)
            sim.run(TIMEOUT_CYCLES)
            elapsed = time.perf_counter() - start
            sim.report(report_path, elapsed_seconds=elapsed)

            accuracy = (100.0 * sim.num_correct_predictions / sim.num_branches
                        if sim.num_branches else 0.0)
            summary.append((report_name, sim.num_cycles, sim.num_branches,
                             accuracy, sim.timed_out))
            print(f"{report_name:24s} cycles={sim.num_cycles:6d}  "
                  f"branches={sim.num_branches:5d}  acc={accuracy:6.2f}%  "
                  f"timeout={sim.timed_out}")

    return summary


if __name__ == '__main__':
    main()