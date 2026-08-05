import re

OPCODES = {
    'add':  ('R', '0000', '001'),
    'sub':  ('R', '0000', '010'),
    'slt':  ('R', '0000', '100'),
    'addi': ('I', '0001', None),
    'li':   ('I', '0010', None),
    'lui':  ('I', '0011', None),
    'lw':   ('I', '0100', None),
    'sw':   ('I', '0101', None),
    'beq':  ('I', '1010', None),
    'bne':  ('I', '1011', None),
    'jmp':  ('J', '1110', None),
    'jal':  ('J', '1111', None),
}

BRANCH_MNEMONICS = {'beq', 'bne'}
JUMP_MNEMONICS = {'jmp', 'jal'}


class AsmError(Exception):
    pass


def _reg_num(tok):
    tok = tok.strip().rstrip(',')
    m = re.match(r'^rx([0-7])$', tok)
    if not m:
        raise AsmError(f"Invalid register: '{tok}' (must be rx0 to rx7)")
    return int(m.group(1))


def _to_bits(value, width):
    mask = (1 << width) - 1
    return format(value & mask, '0{}b'.format(width))


def _strip_comment(line):
    idx = line.find('#')
    if idx != -1:
        line = line[:idx]
    return line.strip()


class _Line:
    __slots__ = ('label', 'mnemonic', 'operands', 'raw', 'lineno')

    def __init__(self, label, mnemonic, operands, raw, lineno):
        self.label = label
        self.mnemonic = mnemonic
        self.operands = operands
        self.raw = raw
        self.lineno = lineno


def _parse_lines(text):
    lines = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        code = _strip_comment(raw)
        if not code:
            continue
        label = None
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$', code)
        if m:
            label = m.group(1)
            code = m.group(2).strip()
        if not code:
            lines.append(_Line(label, None, None, raw, lineno))
            continue
        parts = code.split(None, 1)
        mnemonic = parts[0].lower()
        operand_str = parts[1] if len(parts) > 1 else ''
        operands = [op.strip() for op in operand_str.split(',') if op.strip()]
        lines.append(_Line(label, mnemonic, operands, raw, lineno))
    return lines


def assemble(text):
    raw_lines = _parse_lines(text)

    merged = []
    pending_label = None
    for ln in raw_lines:
        if ln.mnemonic is None:
            if ln.label:
                if pending_label is not None:
                    raise AsmError(
                        f"Two consecutive labels without instruction at line {ln.lineno}: '{ln.label}'")
                pending_label = ln.label
            continue
        label = ln.label
        if pending_label is not None:
            if label is not None:
                raise AsmError(f"Two labels for one instruction at line {ln.lineno}")
            label = pending_label
            pending_label = None
        merged.append(_Line(label, ln.mnemonic, ln.operands, ln.raw, ln.lineno))
    if pending_label is not None:
        raise AsmError(f"Label '{pending_label}' not attached to any instruction")

    labels = {}
    for addr, ln in enumerate(merged):
        if ln.label:
            if ln.label in labels:
                raise AsmError(f"Duplicate label '{ln.label}' at line {ln.lineno}")
            labels[ln.label] = addr

    if len(merged) > 256:
        raise AsmError("Number of instructions exceeds 256 (instruction memory space)")

    encoded = []
    for addr, ln in enumerate(merged):
        word = _encode_instruction(ln, addr, labels)
        encoded.append({
            'addr': addr,
            'word': word,
            'raw': ln.raw.strip(),
            'mnemonic': ln.mnemonic,
        })
    return encoded, labels


def _resolve_imm(tok, width, addr, labels, lineno, raw):
    tok = tok.strip()
    if tok in labels:
        value = labels[tok] - addr
    else:
        try:
            value = int(tok, 0)
        except ValueError:
            raise AsmError(f"Invalid operand '{tok}' at line {lineno}: {raw}")
    lo = -(1 << (width - 1))
    hi = (1 << (width - 1)) - 1
    if not (lo <= value <= hi):
        raise AsmError(
            f"Immediate value {value} out of range {lo}..{hi} at line {lineno}: {raw}")
    return value


def _encode_instruction(ln, addr, labels):
    mnemonic = ln.mnemonic
    if mnemonic not in OPCODES:
        raise AsmError(f"Unknown instruction '{mnemonic}' at line {ln.lineno}: {ln.raw}")
    fmt, opcode, func = OPCODES[mnemonic]
    ops = ln.operands

    try:
        if fmt == 'R':
            if len(ops) != 3:
                raise AsmError(f"Instruction {mnemonic} requires 3 operands")
            rd, rs, rt = _reg_num(ops[0]), _reg_num(ops[1]), _reg_num(ops[2])
            bits = opcode + _to_bits(rd, 3) + _to_bits(rs, 3) + _to_bits(rt, 3) + func

        elif fmt == 'I':
            if mnemonic in ('li', 'lui'):
                if len(ops) != 2:
                    raise AsmError(f"Instruction {mnemonic} requires 2 operands")
                rd = _reg_num(ops[0])
                rs = 0
                imm = _resolve_imm(ops[1], 6, addr, labels, ln.lineno, ln.raw)
            elif mnemonic in ('lw', 'sw', 'addi'):
                if len(ops) != 3:
                    raise AsmError(f"Instruction {mnemonic} requires 3 operands")
                rd = _reg_num(ops[0])
                rs = _reg_num(ops[1])
                imm = _resolve_imm(ops[2], 6, addr, labels, ln.lineno, ln.raw)
            elif mnemonic in ('beq', 'bne'):
                if len(ops) != 3:
                    raise AsmError(f"Instruction {mnemonic} requires 3 operands")
                rd = _reg_num(ops[0])
                rs = _reg_num(ops[1])
                imm = _resolve_imm(ops[2], 6, addr, labels, ln.lineno, ln.raw)
            else:
                raise AsmError(f"Unknown I-format instruction: {mnemonic}")
            bits = opcode + _to_bits(rd, 3) + _to_bits(rs, 3) + _to_bits(imm, 6)

        elif fmt == 'J':
            if len(ops) != 1:
                raise AsmError(f"Instruction {mnemonic} requires 1 operand")
            imm = _resolve_imm(ops[0], 12, addr, labels, ln.lineno, ln.raw)
            bits = opcode + _to_bits(imm, 12)
        else:
            raise AsmError("Invalid instruction format")
    except AsmError:
        raise
    except Exception as e:  # noqa
        raise AsmError(f"Error at line {ln.lineno} ({ln.raw}): {e}")

    if len(bits) != 16:
        raise AsmError(f"Incorrect bit length for line {ln.lineno}: {ln.raw}")
    return int(bits, 2)


def disassemble(word):
    opcode = (word >> 12) & 0xF
    opcode_bits = format(opcode, '04b')
    for name, (fmt, oc, func) in OPCODES.items():
        if oc != opcode_bits:
            continue
        if fmt == 'R':
            f = word & 0x7
            if func is not None and format(f, '03b') != func:
                continue
            rd = (word >> 9) & 0x7
            rs = (word >> 6) & 0x7
            rt = (word >> 3) & 0x7
            return f"{name} rx{rd}, rx{rs}, rx{rt}"
        elif fmt == 'I':
            rd = (word >> 9) & 0x7
            rs = (word >> 6) & 0x7
            imm = word & 0x3F
            if imm & 0x20:
                imm -= 0x40
            if name in ('li', 'lui'):
                return f"{name} rx{rd}, {imm}"
            return f"{name} rx{rd}, rx{rs}, {imm}"
        elif fmt == 'J':
            imm = word & 0xFFF
            if imm & 0x800:
                imm -= 0x1000
            return f"{name} {imm}"
    return f"??? (0x{word:04X})"