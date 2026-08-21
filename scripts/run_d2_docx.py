"""Generate D2 docx from the workspace markdown report.

This wrapper avoids passing Chinese filenames through PowerShell command line.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md_report_to_docx import convert

WORKSPACE = r"c:\Users\hj\CodeBuddy\20260819144818"
MD_PATH = os.path.join(WORKSPACE, "第2天报告_20260820.md")
OUT_PATH = os.path.join(WORKSPACE, "第2天报告_20260820.docx")

convert(MD_PATH, OUT_PATH)
