#!/usr/bin/env python3
"""Convert .schx schematic files into simple SPICE netlists."""
import xml.etree.ElementTree as ET
import math
import os
import re

BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
SCHEM_DIR = os.path.join(BASE_DIR, 'SchemToImport', 'Examples')
OUT_DIR = os.path.join(BASE_DIR, 'PedalNetlists')

UNIT_MAP = {
    'Ω': '', 'kΩ': 'k', 'MΩ': 'meg',
    'F': '', 'uF': 'u', 'μF': 'u', 'nF': 'n', 'pF': 'p',
    'H': 'H', 'mH': 'mH',
    'V': '', 'A': '', 'mA': 'mA', 'uA': 'uA', 'nA': 'nA'
}
FLOAT_RE = re.compile(r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)')

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

def symbol_pins(pos, points):
    px, py = pos
    d = min(math.hypot(px - x, py - y) for x, y in points)
    return [p for p in points if abs(math.hypot(px - p[0], py - p[1]) - d) < 1e-6]

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

    elements = []
    params = []
    for sym in symbols:
        pins = symbol_pins(sym['pos'], points)
        nets = [node_of(p) for p in pins]
        attrs = sym['attrs']
        name = attrs.get('Name', 'X')
        stype = sym['type']
        if 'Resistor' in stype and len(nets) == 2:
            val = parse_value(attrs.get('Resistance', '1k'))
            elements.append(f"R{name} N{nets[0]} N{nets[1]} {val}")
        elif 'Capacitor' in stype and len(nets) == 2:
            val = parse_value(attrs.get('Capacitance', '1u'))
            elements.append(f"C{name} N{nets[0]} N{nets[1]} {val}")
        elif ('VoltageSource' in stype or 'Input' in stype or 'Rail' in stype) and len(nets) >= 2:
            val = parse_value(attrs.get('Voltage', '0')) or '0'
            elements.append(f"V{name} N{nets[0]} N{nets[1]} {val}")
        elif 'Diode' in stype and len(nets) == 2:
            model = attrs.get('PartNumber', 'D')
            elements.append(f"D{name} N{nets[0]} N{nets[1]} {model}")
        elif 'BipolarJunctionTransistor' in stype and len(nets) == 3:
            model = attrs.get('PartNumber', 'Q')
            elements.append(f"Q{name} N{nets[0]} N{nets[1]} N{nets[2]} {model}")
        elif 'Speaker' in stype and len(nets) == 2:
            elements.append(f"R{name} N{nets[0]} N{nets[1]} 8")
        elif 'Potentiometer' in stype and len(nets) == 3:
            pos_param = f"P_{name}"
            params.append(f".param {pos_param} = {attrs.get('Wipe', '0.5')}")
            r = parse_value(attrs.get('Resistance', '100k'))
            elements.append(f"R{name}a N{nets[0]} N{nets[1]} {r}")
            elements.append(f"R{name}b N{nets[1]} N{nets[2]} {r}")

    header = ['* generated from ' + os.path.basename(path)] + params
    footer = [
        '.tran 2u 100m 80m',
        '.op',
        '.control',
        '  run',
        '  quit',
        '.endc',
        '.end'
    ]
    return '\n'.join(header + elements + footer) + '\n'

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
