#!/usr/bin/env python3
"""Convert .schx schematic files into simple SPICE netlists."""
import xml.etree.ElementTree as ET
import math
import os
import re

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
SCHEM_DIR = os.path.join(BASE_DIR, 'SchemToImport', 'Examples')
OUT_DIR = os.path.join(BASE_DIR, 'PedalNetlists')
MODELS_DIR = os.path.join(BASE_DIR, 'PartModels')
MODEL_INDEX = os.path.join(MODELS_DIR, 'ModelDirectory.txt')
SUBCKT_INDEX = os.path.join(MODELS_DIR, 'SubcircuitDirectory.txt')

UNIT_MAP = {
    'Ω': '', 'kΩ': 'k', 'MΩ': 'meg',
    'F': '', 'uF': 'u', 'μF': 'u', 'nF': 'n', 'pF': 'p',
    'H': 'H', 'mH': 'mH',
    'V': '', 'A': '', 'mA': 'mA', 'uA': 'uA', 'nA': 'nA'
}
FLOAT_RE = re.compile(r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)')

# load model/subcircuit directories once
def _load_index(fname: str):
    entries: list[tuple[str, str, bool]] = []
    if not os.path.exists(fname):
        return entries
    with open(fname, 'r', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue
            path, _line, stmt = parts
            if path.startswith('./'):
                path = os.path.join(BASE_DIR, path[2:])
            tokens = stmt.strip().split()
            if len(tokens) < 2:
                continue
            directive = tokens[0].lower()
            if directive in ('.model', '.subckt'):
                name = tokens[1]
                entries.append((path, name, directive == '.subckt'))
    return entries

MODEL_ENTRIES = _load_index(MODEL_INDEX)
SUBCKT_ENTRIES = _load_index(SUBCKT_INDEX)

def find_model(part: str):
    """Return (path, name, is_subckt) for *part* if present in indices."""
    if not part:
        return None
    target = part.upper()
    for path, name, is_sub in SUBCKT_ENTRIES:
        if target in name.upper() or target in os.path.basename(path).upper():
            return path, name, True
    for path, name, is_sub in MODEL_ENTRIES:
        if target in name.upper() or target in os.path.basename(path).upper():
            return path, name, False
    return None

def sanitize(name: str) -> str:
    """Convert schematic names into safe SPICE identifiers."""
    return re.sub(r'\W+', '_', name)

def float_value(text: str) -> float | None:
    """Return the numeric portion of a value string as a float."""
    val = parse_value(text)
    if val is None:
        return None
    m = FLOAT_RE.search(val)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None

def parse_value(text: str) -> str | None:
    text = text.replace('µ', 'u')
    if '∞' in text:
        return None
    m = FLOAT_RE.search(text)
    if not m:
        return text
    number = m.group(1)
    unit = text[m.end():].strip()
    if unit in UNIT_MAP:
        unit = UNIT_MAP[unit]
    return f"{number}{unit}"

class UnionFind:
    def __init__(self):
        self.parent = {}
    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

def collect_net_ids(wires):
    uf = UnionFind()
    for a, b in wires:
        uf.union(a, b)
    net_ids = {}
    next_id = 1
    for pt in uf.parent:
        r = uf.find(pt)
        if r not in net_ids:
            net_ids[r] = next_id
            next_id += 1
    def node(pt):
        return net_ids[uf.find(pt)]
    return node

def symbol_pins(pos, points, radius=35):
    """Return all wire points within *radius* of *pos*"""
    px, py = pos
    return [p for p in points if math.hypot(px - p[0], py - p[1]) <= radius]

def process_file(path):
    root = ET.parse(path).getroot()
    wires = []
    symbols = []
    for elem in root:
        typ = elem.attrib.get('Type', '')
        if 'Circuit.Wire' in typ:
            a = tuple(map(int, elem.attrib['A'].split(',')))
            b = tuple(map(int, elem.attrib['B'].split(',')))
            wires.append((a, b))
        elif 'Circuit.Symbol' in typ:
            comp = elem.find('Component')
            pos = tuple(map(int, elem.attrib['Position'].split(',')))
            symbols.append({'type': comp.attrib.get('_Type', ''), 'attrs': comp.attrib, 'pos': pos})

    node_of = collect_net_ids(wires)
    points = list({pt for w in wires for pt in w})

    # map of numerical node -> named node
    aliases: dict[int, str] = {}
    rails: dict[str, str] = {}

    # first identify ground and rail nets
    for sym in symbols:
        stype = sym['type']
        pins = symbol_pins(sym['pos'], points)
        nets = sorted({node_of(p) for p in pins})
        attrs = sym['attrs']

        if 'Ground' in stype:
            for n in nets:
                aliases[n] = '0'
        elif 'Rail' in stype:
            val = attrs.get('Voltage', '0')
            v = float_value(val) or 0.0
            name = 'VCC' if abs(v - 9) < 0.2 else 'VB' if abs(v - 4.5) < 0.2 else '0' if abs(v) < 1e-6 else None
            if name:
                for n in nets:
                    aliases[n] = name
                rails[name] = parse_value(val) or '0'

    # determine input node name
    input_net = None
    for sym in symbols:
        if 'Input' in sym['type']:
            pins = symbol_pins(sym['pos'], points)
            nets = sorted({node_of(p) for p in pins})
            for n in nets:
                if aliases.get(n) != '0':
                    aliases[n] = 'IN'
                    input_net = n
            break

    def node(n: int) -> str:
        return aliases.get(n, f'N{n}')

    elements = []
    params = []
    includes = set()

    for sym in symbols:
        pins = symbol_pins(sym['pos'], points)
        nets = sorted({node_of(p) for p in pins})
        attrs = sym['attrs']
        name = sanitize(attrs.get('Name', 'X'))
        stype = sym['type']
        model_info = find_model(attrs.get('PartNumber'))
        model_name = attrs.get('PartNumber')
        if model_info:
            includes.add(f".include \"{model_info[0]}\"")
            model_name = model_info[1]

        if 'Potentiometer' in stype and len(nets) == 3:
            pname = f"P_{name}"
            params.append(f".param {pname} = {attrs.get('Wipe', '0.5')}")
            r = parse_value(attrs.get('Resistance', '100k'))
            elements.append(f"R{name}A {node(nets[0])} {node(nets[1])} {{{r} * (1-{pname})}}")
            elements.append(f"R{name}B {node(nets[1])} {node(nets[2])} {{{r} * {pname}}}")
        elif 'VariableResistor' in stype and len(nets) >= 2:
            pname = f"P_{name}"
            params.append(f".param {pname} = {attrs.get('Wipe', '0.5')}")
            r = parse_value(attrs.get('Resistance', '1k'))
            elements.append(f"R{name} {node(nets[0])} {node(nets[1])} {{{r} * {pname}}}")
        elif 'Resistor' in stype and len(nets) == 2:
            val = parse_value(attrs.get('Resistance', '1k'))
            elements.append(f"R{name} {node(nets[0])} {node(nets[1])} {val}")
        elif 'Capacitor' in stype and len(nets) == 2:
            val = parse_value(attrs.get('Capacitance', '1u'))
            elements.append(f"C{name} {node(nets[0])} {node(nets[1])} {val}")
        elif 'VoltageSource' in stype and len(nets) >= 2:
            val = parse_value(attrs.get('Voltage', '0')) or '0'
            elements.append(f"V{name} {node(nets[0])} {node(nets[1])} {val}")
        elif 'Diode' in stype and len(nets) == 2:
            model = model_name or 'D'
            elements.append(f"D{name} {node(nets[0])} {node(nets[1])} {model}")
        elif 'BipolarJunctionTransistor' in stype and len(nets) >= 3:
            model = model_name or 'Q'
            pins = [node(n) for n in nets[:3]]
            elements.append(f"Q{name} {' '.join(pins)} {model}")
        elif 'FieldEffectTransistor' in stype and len(nets) >= 3:
            model = model_name or 'JFET'
            pins = [node(n) for n in nets[:3]]
            elements.append(f"J{name} {' '.join(pins)} {model}")
        elif any(t in stype for t in ['MOSFET', 'MOS', 'NMOS', 'PMOS']) and len(nets) >= 4:
            model = model_name or 'MOS'
            pins = [node(n) for n in nets[:4]]
            elements.append(f"M{name} {' '.join(pins)} {model}")
        elif 'OpAmp' in stype and len(nets) >= 5:
            subckt = model_name or 'OPAMP'
            pins = [node(n) for n in nets]
            elements.append(f"X{name} {' '.join(pins)} {subckt}")
        elif model_info:
            pins = [node(n) for n in nets]
            elements.append(f"X{name} {' '.join(pins)} {model_name}")
        elif 'Speaker' in stype and len(nets) == 2:
            elements.append(f"R{name} {node(nets[0])} {node(nets[1])} 8")

    header = []
    header.extend(params)
    header.extend(sorted(includes))
    header.append(f"* generated from {os.path.basename(path)}")

    globalsrc = []
    if 'VCC' in rails:
        globalsrc.append(f"VCC VCC 0 DC {rails['VCC']}")
    else:
        globalsrc.append("VCC VCC 0 DC 9")
    globalsrc.append("VIN IN 0 SIN(0 50m 500)")

    footer = [
        '.tran 2u 100m 80m',
        '.op',
        '.control',
        '  run',
        '  quit',
        '.endc',
        '.end'
    ]

    lines = header + globalsrc + elements + footer
    return '\n'.join(lines) + '\n'

def main():
    for fname in os.listdir(SCHEM_DIR):
        if not fname.endswith('.schx'):
            continue
        src = os.path.join(SCHEM_DIR, fname)
        base = os.path.splitext(fname)[0].replace(' ', '_')
        dst = os.path.join(OUT_DIR, base + '.cir')
        text = process_file(src)
        with open(dst, 'w') as f:
            f.write(text)
        print('wrote', dst)

if __name__ == '__main__':
    main()
