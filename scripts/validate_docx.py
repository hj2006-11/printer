# -*- coding: utf-8 -*-
"""校验生成的 docx：XML 良构性 + 结构一致性（对所有 *.docx）。"""
import zipfile, xml.dom.minidom as m, glob, os, re

files = glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "*.docx"))
assert files, "no docx found"
for p in files:
    print("validating:", os.path.basename(p))
    z = zipfile.ZipFile(p)
    for n in z.namelist():
        if n.endswith((".xml", ".rels")):
            m.parseString(z.read(n))
    doc = z.read("word/document.xml").decode("utf-8")
    for w in re.findall(r'<w:tblW w:w="(\d+)"', doc):
        assert int(w) == 9026, f"table width mismatch {w} in {p}"
    print("  OK: tables", doc.count("<w:tbl>"), "| paragraphs", doc.count("<w:p>"))
print("ALL DOCX VALIDATION PASSED")
