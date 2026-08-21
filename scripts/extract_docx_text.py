# -*- coding: utf-8 -*-
"""Extract paragraph text from docx files (zero-dependency).
Usage: python extract_docx_text.py <directory> [output_file] [name_substr]
"""
import sys, os, zipfile
from xml.etree import ElementTree as ET

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

def extract(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8')
    root = ET.fromstring(xml)
    out = []
    for p in root.iter('{%s}p' % NS['w']):
        texts = []
        for node in p.iter():
            if node.tag in ('{%s}t' % NS['w'], '{%s}delText' % NS['w']):
                texts.append(node.text or '')
        line = ''.join(texts).strip()
        out.append(line)
    return out

if __name__ == '__main__':
    directory = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else ''
    substr = sys.argv[3] if len(sys.argv) > 3 else ''
    lines = []
    for name in sorted(os.listdir(directory)):
        if not name.lower().endswith('.docx') or '~$' in name:
            continue
        if substr and substr not in name:
            continue
        path = os.path.join(directory, name)
        lines.append('=' * 70)
        lines.append('FILE: ' + name)
        lines.append('=' * 70)
        try:
            for line in extract(path):
                lines.append(line)
        except Exception as e:
            lines.append('ERROR: %s' % e)
        lines.append('')
    text = '\n'.join(lines)
    if out_file:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print('written to', out_file)
    else:
        sys.stdout.write(text)
