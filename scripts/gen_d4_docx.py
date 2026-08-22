"""Generate D4 deliverable as docx (wrapper to avoid console encoding issues)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md_to_docx_v2 import convert

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

jobs = [
    ("第4天报告_20260822.md", "第4天报告_20260822.docx"),
]

for md, docx in jobs:
    md_path = os.path.join(ROOT, md)
    docx_path = os.path.join(ROOT, docx)
    print(f"converting {md_path} -> {docx_path}")
    convert(md_path, docx_path)
print("all done")
