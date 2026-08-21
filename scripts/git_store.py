# -*- coding: utf-8 -*-
"""使用 dulwich（纯 Python git）完成本地仓库 init + add + commit + push。
用法：
  python scripts/git_store.py init
  python scripts/git_store.py add
  python scripts/git_store.py commit ["<message>"]
  python scripts/git_store.py push <remote-url>
"""
import os
import sys

import dulwich.client as dclient
from dulwich import porcelain


class WinSSHVendor(dclient.SubprocessSSHVendor):
    """Windows OpenSSH 版本较旧不支持 `-o SetEnv`，强制关闭 git 协议版本协商。"""

    def run_command(self, host, command, username=None, port=None, password=None,
                    key_filename=None, ssh_command=None, protocol_version=None):
        if sys.platform == "win32":
            protocol_version = 0
        return super().run_command(
            host, command, username=username, port=port, password=password,
            key_filename=key_filename, ssh_command=ssh_command,
            protocol_version=protocol_version,
        )


dclient.get_ssh_vendor = lambda: WinSSHVendor()


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
        repo = porcelain.open_repo(root)
        if len(sys.argv) >= 3:
            msg = sys.argv[2]
        else:
            msg = "D3: 接口约定v1.0+数据模型+第3天报告+代码契约化"
        author = os.environ.get("GIT_AUTHOR", "CCPC Printer <ccpc@local>")
        cid = porcelain.commit(repo, message=msg, author=author.encode("utf-8"),
                               committer=author.encode("utf-8"))
        print("committed:", cid.decode("ascii"))
    elif cmd == "push":
        if len(sys.argv) < 3:
            print("usage: git_store.py push <remote-url>")
            return
        repo = porcelain.open_repo(root)
        url = sys.argv[2]
        try:
            porcelain.remote_add(repo, "origin", url)
            print("remote origin added:", url)
        except porcelain.RemoteExists:
            print("remote origin already exists")
        branches = [r for r in repo.refs.keys(base=b"refs/heads")]
        if not branches:
            print("no local branch found")
            return
        branch = branches[0].decode("ascii")
        refspec = f"refs/heads/{branch}:refs/heads/{branch}"
        print("pushing", refspec)
        res = porcelain.push(repo, url, refspec)
        print("push result:", res)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
