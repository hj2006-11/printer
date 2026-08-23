# -*- coding: utf-8 -*-
"""D5 临时脚本2：删除临时文件 + 从索引/工作区清理产物 + 重做暂存"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from dulwich import porcelain
from dulwich import index as dul_index

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. 删除工作区临时文件（中文名不受 PowerShell 干扰）
tmp_files = [
    '_tmp_图片.md', '_tmp_模版.md', '_tmp_题目.md',
    'printsvc/_bad1.json', 'printsvc/_bad2.json',
    'printsvc/_code.json', 'printsvc/_ticket.json',
    'printsvc/_gen_code.py',
    'scripts/_extract_docx.py', 'scripts/_tmp_diff_d4.py',
    'scripts/_tmp_git_d5.py',
]
for f in tmp_files:
    p = os.path.join(root, f)
    if os.path.exists(p):
        os.remove(p)
        print('removed:', f)

# 2. 从索引移除运行产物（output/、port.txt 应被 .gitignore 忽略，若被误暂存则移除）
repo = porcelain.open_repo(root)
idx_path = os.path.join(root, '.git', 'index')
idx = dul_index.Index(idx_path)
drop = []
for path in list(idx._byname.keys()):
    p = path.decode('utf-8')
    if p.startswith('printsvc/output/') or p == 'printsvc/port.txt' or p == 'printsvc/pid.txt':
        idx._byname.pop(path)
        drop.append(p)
idx.write()
print('dropped from index:', drop)

# 3. 重新暂存
porcelain.add(repo, '.')
status = porcelain.status(repo)
staged = sorted(s.decode() for s in status.staged.get('add', [])) + \
         sorted(s.decode() for s in status.staged.get('modify', []))
print('staged:', staged)
deleted = sorted(s.decode() for s in status.staged.get('delete', []))
print('deleted:', deleted)
