import sys
import time
from simulator import TinyBASUSimulator as Simulator
def main():
    if len(sys.argv) != 6:
        print("Usage: python main.py [timeout_cycles] "
              "[prediction_method] [inst_file] [data_file] [report_file]")
        print("  prediction_method is one of: ST, SN, D1, D2, IQ")
        sys.exit(1)

    timeout_cycles = int(sys.argv[1])
    prediction_method = sys.argv[2]
    inst_file = sys.argv[3]
    data_file = sys.argv[4]
    report_file = sys.argv[5]

    simulator = Simulator(prediction_method)

    start = time.perf_counter()
    simulator.parse_instruction(inst_file)
    simulator.init_memory(data_file)
    simulator.run(timeout_cycles)
    elapsed = time.perf_counter() - start

    text = simulator.report(report_file, elapsed_seconds=elapsed)
    print(text)


if __name__ == '__main__':
    main()