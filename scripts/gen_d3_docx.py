"""Generate D3 deliverables as docx (wrapper to avoid console encoding issues)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md_to_docx_v2 import convert

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

jobs = [
    ("第3天报告_20260821.md", "第3天报告_20260821.docx"),
    ("接口书面约定_20260821.md", "接口书面约定_20260821.docx"),
    ("数据模型_20260821.md", "数据模型_20260821.docx"),
    ("03_项目备忘_20260821.md", "03_项目备忘_20260821.docx"),
]

for md, docx in jobs:
    md_path = os.path.join(ROOT, md)
    docx_path = os.path.join(ROOT, docx)
    print(f"converting {md_path} -> {docx_path}")
    convert(md_path, docx_path)
print("all done")
