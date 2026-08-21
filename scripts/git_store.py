# -*- coding: utf-8 -*-
"""使用 dulwich（纯 Python git）完成本地仓库 init + add + commit。
用法：
  python scripts/git_store.py init
  python scripts/git_store.py add
  python scripts/git_store.py commit "<message>"
"""
import os
import sys

from dulwich import porcelain


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if cmd == "init":
        repo = porcelain.init(root)
        print("git repo initialized at", root)
    elif cmd == "add":
        repo = porcelain.open_repo(root)
        porcelain.add(repo, ".")
        print("staged all files (respecting .gitignore)")
        status = porcelain.status(repo)
        print("staged:", sorted(status.staged.get("add", []))[:20])
    elif cmd == "commit":
        if len(sys.argv) < 3:
            print("usage: git_store.py commit <message>")
            return
        repo = porcelain.open_repo(root)
        msg = sys.argv[2]
        author = os.environ.get("GIT_AUTHOR", "CCPC Printer <ccpc@local>")
        cid = porcelain.commit(repo, message=msg, author=author.encode("utf-8"),
                               committer=author.encode("utf-8"))
        print("committed:", cid.decode("ascii"))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
