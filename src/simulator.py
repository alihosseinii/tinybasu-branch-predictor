from assembler import assemble, disassemble

WORD_MASK = 0xFFFF
NUM_REGS = 8
MEM_SIZE = 512
INSTR_MEM_LIMIT = 256
BRANCH_PENALTY = 3 

BRANCH_OPS = {0b1010: 'beq', 0b1011: 'bne'}
JUMP_OPS = {0b1110: 'jmp', 0b1111: 'jal'}


def sign_extend(value, bits):
    if value & (1 << (bits - 1)):
        value -= (1 << bits)
    return value


def to_u16(value):
    return value & WORD_MASK


def decode(word):
    opcode = (word >> 12) & 0xF
    if opcode == 0b0000:  # R-format
        rd = (word >> 9) & 0x7
        rs = (word >> 6) & 0x7
        rt = (word >> 3) & 0x7
        func = word & 0x7
        return {'fmt': 'R', 'opcode': opcode, 'rd': rd, 'rs': rs, 'rt': rt, 'func': func}
    elif opcode in JUMP_OPS:  # J-format
        imm = sign_extend(word & 0xFFF, 12)
        return {'fmt': 'J', 'opcode': opcode, 'imm': imm}
    else:  # I-format
        rd = (word >> 9) & 0x7
        rs = (word >> 6) & 0x7
        imm = sign_extend(word & 0x3F, 6)
        return {'fmt': 'I', 'opcode': opcode, 'rd': rd, 'rs': rs, 'imm': imm}


class BranchPredictor:
    name = 'base'

    def predict(self, pc):
        raise NotImplementedError

    def update(self, pc, taken):
        raise NotImplementedError


class StaticTaken(BranchPredictor):
    name = 'ST'

    def predict(self, pc):
        return True

    def update(self, pc, taken):
        pass


class StaticNotTaken(BranchPredictor):
    name = 'SN'

    def predict(self, pc):
        return False

    def update(self, pc, taken):
        pass


class Dynamic1Bit(BranchPredictor):
    name = 'D1'

    def __init__(self):
        self.table = {}

    def predict(self, pc):
        state = self.table.get(pc, 0)
        return state == 1

    def update(self, pc, taken):
        self.table[pc] = 1 if taken else 0


class Dynamic2Bit(BranchPredictor):
    name = 'D2'
    STRONGLY_NOT_TAKEN, WEAKLY_NOT_TAKEN, WEAKLY_TAKEN, STRONGLY_TAKEN = range(4)

    def __init__(self):
        self.table = {} 

    def predict(self, pc):
        state = self.table.get(pc, self.WEAKLY_NOT_TAKEN)
        return state >= self.WEAKLY_TAKEN

    def update(self, pc, taken):
        state = self.table.get(pc, self.WEAKLY_NOT_TAKEN)
        if taken:
            state = min(state + 1, self.STRONGLY_TAKEN)
        else:
            state = max(state - 1, self.STRONGLY_NOT_TAKEN)
        self.table[pc] = state


class HeuristicIQ(BranchPredictor):
    name = 'IQ'
    MAX_STATE = 7
    INIT_STATE = 4 

    def __init__(self):
        self.table = {}

    def predict(self, pc):
        state = self.table.get(pc, self.INIT_STATE)
        return state >= 4

    def update(self, pc, taken):
        state = self.table.get(pc, self.INIT_STATE)
        if taken:
            state = min(state + 1, self.MAX_STATE)
        else:
            state = max(state - 1, 0)
        self.table[pc] = state


PREDICTORS = {
    'ST': StaticTaken,
    'SN': StaticNotTaken,
    'D1': Dynamic1Bit,
    'D2': Dynamic2Bit,
    'IQ': HeuristicIQ,
}


class TinyBASUSimulator:
    def __init__(self, prediction_method):
        if prediction_method not in PREDICTORS:
            raise ValueError(
                f"Invalid prediction method '{prediction_method}'. "
                f"Valid options: {', '.join(PREDICTORS)}")
        self.prediction_method = prediction_method
        self.predictor = PREDICTORS[prediction_method]()

        self.regs = [0] * NUM_REGS
        self.memory = [0] * MEM_SIZE
        self.pc = 0
        self.halted = False
        self.timed_out = False

        self.num_cycles = 0
        self.num_instructions = 0
        self.num_executed_instructions = 0 
        self.num_stalls = 0
        self.num_branches = 0
        self.num_correct_predictions = 0
        self.num_jumps = 0

        self.source_lines = {} 
        self._trace = []

    def parse_instruction(self, inst_file):
        with open(inst_file, 'r', encoding='utf-8') as f:
            text = f.read()
        encoded, labels = assemble(text)
        if len(encoded) > INSTR_MEM_LIMIT:
            raise ValueError("Number of instructions exceeds instruction memory space (256)")
        for item in encoded:
            self.memory[item['addr']] = item['word']
            self.source_lines[item['addr']] = item['raw']
        self.num_instructions = len(encoded)
        self.labels = labels
        self.program_end_addr = len(encoded) 
        return encoded, labels

    def init_memory(self, data_file):
        if not data_file:
            return
        with open(data_file, 'r', encoding='utf-8') as f:
            lines = [ln.strip() for ln in f.readlines()]
        for n, line in enumerate(lines, start=1):
            if not line:
                continue
            addr = 255 + n
            if addr >= MEM_SIZE:
                raise ValueError(f"Data address {addr} out of memory range")
            self.memory[addr] = int(line, 16) & WORD_MASK

    def fetch(self):
        instr_addr = self.pc
        word = self.memory[self.pc]
        return instr_addr, word

    def execute(self, instr_addr, fields):
        regs = self.regs
        opcode = fields['opcode']
        next_pc = instr_addr + 1
        branch_info = None 

        if fields['fmt'] == 'R':
            rd, rs, rt, func = fields['rd'], fields['rs'], fields['rt'], fields['func']
            if func == 0b001:      # add
                regs[rd] = to_u16(regs[rs] + regs[rt])
            elif func == 0b010:    # sub
                regs[rd] = to_u16(regs[rs] - regs[rt])
            elif func == 0b100:    # slt
                regs[rd] = 1 if regs[rs] < regs[rt] else 0
            else:
                raise ValueError(f"Invalid func {func:03b} at address {instr_addr}")

        elif opcode == 0b0001:  # addi
            rd, rs, imm = fields['rd'], fields['rs'], fields['imm']
            regs[rd] = to_u16(regs[rs] + imm)

        elif opcode == 0b0010:  # li
            rd, imm = fields['rd'], fields['imm']
            regs[rd] = to_u16(imm)

        elif opcode == 0b0011:  # lui
            rd, imm = fields['rd'], fields['imm']
            regs[rd] = to_u16(imm << 10)

        elif opcode == 0b0100:  # lw
            rd, rs, imm = fields['rd'], fields['rs'], fields['imm']
            addr = to_u16(regs[rs] + imm)
            if addr >= MEM_SIZE:
                raise ValueError(f"Memory address out of range in LW: {addr}")
            regs[rd] = self.memory[addr]

        elif opcode == 0b0101:  # sw
            rd, rs, imm = fields['rd'], fields['rs'], fields['imm']
            addr = to_u16(regs[rs] + imm)
            if addr >= MEM_SIZE:
                raise ValueError(f"Memory address out of range in SW: {addr}")
            self.memory[addr] = regs[rd]

        elif opcode in BRANCH_OPS:  # beq / bne
            rd, rs, imm = fields['rd'], fields['rs'], fields['imm']
            mnemonic = BRANCH_OPS[opcode]
            if mnemonic == 'beq':
                actually_taken = (regs[rd] == regs[rs])
            else:  # bne
                actually_taken = (regs[rd] != regs[rs])

            predicted_taken = self.predictor.predict(instr_addr)
            correct = (predicted_taken == actually_taken)

            if actually_taken:
                next_pc = to_u16(instr_addr + imm)
            else:
                next_pc = instr_addr + 1

            self.predictor.update(instr_addr, actually_taken)
            branch_info = (True, actually_taken, correct)

        elif opcode == 0b1110:  # jmp
            imm = fields['imm']
            next_pc = to_u16(instr_addr + imm)

        elif opcode == 0b1111:  # jal
            imm = fields['imm']
            regs[7] = to_u16(instr_addr + 1)
            next_pc = to_u16(instr_addr + imm)

        else:
            raise ValueError(f"Unknown opcode {opcode:04b} at address {instr_addr}")

        return next_pc, branch_info

    def run(self, timeout_cycles):
        while True:
            if self.num_cycles > timeout_cycles:
                self.timed_out = True
                break

            instr_addr, word = self.fetch()

            if instr_addr >= self.program_end_addr or word == 0:
                self.halted = True
                break

            fields = decode(word)
            next_pc, branch_info = self.execute(instr_addr, fields)

            self.num_executed_instructions += 1
            self.num_cycles += 1 

            is_jump = fields['opcode'] in JUMP_OPS

            if branch_info is not None:
                _, taken, correct = branch_info
                self.num_branches += 1
                if correct:
                    self.num_correct_predictions += 1
                else:
                    self.num_cycles += BRANCH_PENALTY
                    self.num_stalls += 1
            elif is_jump:
                self.num_cycles += BRANCH_PENALTY
                self.num_stalls += 1
                self.num_jumps += 1

            self.pc = next_pc

        return self

    def _no_prediction_cycles(self):
        return self.num_executed_instructions + BRANCH_PENALTY * (
            self.num_branches + self.num_jumps)

    def report(self, report_file, elapsed_seconds=0.0):
        ipc = (self.num_executed_instructions / self.num_cycles) if self.num_cycles else 0.0
        accuracy = (100.0 * self.num_correct_predictions / self.num_branches
                    if self.num_branches else 0.0)
        no_pred_cycles = self._no_prediction_cycles()
        speedup = (no_pred_cycles / self.num_cycles) if self.num_cycles else 0.0

        lines = []
        lines.append("=" * 60)
        lines.append("TinyBASU Processor Simulation Report")
        lines.append("=" * 60)
        lines.append(f"Branch prediction algorithm          : {self.prediction_method}")
        lines.append(f"Simulation execution time (seconds)  : {elapsed_seconds:.6f}")
        lines.append(f"Static assembly instructions count   : {self.num_instructions}")
        lines.append(f"Total cycles consumed                : {self.num_cycles}")
        lines.append(f"Total executed instructions          : {self.num_executed_instructions}")
        lines.append(f"IPC (instructions per cycle)         : {ipc:.4f}")
        lines.append("")
        lines.append("Register contents after last cycle:")
        for i, v in enumerate(self.regs):
            lines.append(f"  rx{i} = {v} (0x{v:04X})")
        lines.append(f"Final PC value                       : {self.pc}")
        lines.append("")
        lines.append(f"Number of stalls due to branches     : {self.num_stalls}")
        lines.append(f"Total conditional branches executed  : {self.num_branches}")
        lines.append(f"Number of correct predictions        : {self.num_correct_predictions}")
        lines.append(f"Branch prediction accuracy (%)       : {accuracy:.2f}")
        lines.append(f"Estimated cycles without prediction  : {no_pred_cycles}")
        lines.append(f"Speedup over no prediction           : {speedup:.4f}x")
        lines.append("")
        lines.append(f"Execution status                     : "
                      f"{'timeout (possible bug/infinite loop)' if self.timed_out else 'normal program termination'}")
        lines.append("=" * 60)

        text = "\n".join(lines) + "\n"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(text)
        return text