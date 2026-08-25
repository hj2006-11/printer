# -*- coding: utf-8 -*-
"""使用 dulwich（纯 Python git）完成本地仓库 init + status + add + commit + push。
用法：
  python scripts/git_store.py init
  python scripts/git_store.py status
  python scripts/git_store.py add [paths...]
  python scripts/git_store.py commit ["<message>"]
  python scripts/git_store.py push <remote-url>
"""
import fnmatch
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


def _dir_has_visible(root, rel):
    """目录内是否含未被忽略的文件（用于过滤 dulwich 对空壳目录的误报）。"""
    full = os.path.join(root, rel)
    if not os.path.isdir(full):
        return True
    for dirpath, dirnames, filenames in os.walk(full):
        for d in list(dirnames):
            r = os.path.relpath(os.path.join(dirpath, d), root).replace(os.sep, "/")
            if _gitignored(r + "/", root):
                dirnames.remove(d)
        for fn in filenames:
            r = os.path.relpath(os.path.join(dirpath, fn), root).replace(os.sep, "/")
            if not _gitignored(r, root):
                return True
    return False


def _gitignored(path, root):
    """按 .gitignore 规则判断路径是否被忽略。

    dulwich 对 `printsvc/dist/` 这类目录模式的 ignore 匹配有怪癖（误报 untracked），
    这里用简单规则解析二次过滤（本项目 .gitignore 均为基础模式，无 **/! 等高级语法）。
    """
    try:
        rules = []
        with open(os.path.join(root, ".gitignore"), encoding="utf-8") as f:
            for raw in f:
                # git 不支持行内注释：剥离 ` #` 之后的注释部分
                line = raw.split(" #", 1)[0].strip()
                if not line or line.startswith("#"):
                    continue
                rules.append(line)
    except OSError:
        return False
    q = path.replace("\\", "/").rstrip("/")
    for r in rules:
        if r.endswith("/"):  # 目录规则：匹配任意层级的同名目录
            base = r.rstrip("/")
            if q == base or q.startswith(base + "/") or base in q.split("/"):
                return True
        elif fnmatch.fnmatch(q, r) or fnmatch.fnmatch(q.split("/")[-1], r):
            return True
    return False


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if cmd == "init":
        repo = porcelain.init(root)
        print("git repo initialized at", root)
    elif cmd == "status":
        repo = porcelain.open_repo(root)
        head = repo.head()
        print("HEAD:", head.decode("ascii")[:8])
        st = porcelain.status(repo)
        untracked = []
        for p in st.untracked:
            s = p.decode("utf-8") if isinstance(p, bytes) else p
            if s.endswith(("\\", "/")) and not _dir_has_visible(root, s.rstrip("/\\")):
                continue  # 空壳目录（内部全为忽略项）
            if not _gitignored(s, root):
                untracked.append(s)
        dirty = False
        for label, items in (
            ("staged(add)", st.staged.get("add") or ()),
            ("staged(modify)", st.staged.get("modify") or ()),
            ("staged(delete)", st.staged.get("delete") or ()),
            ("unstaged", st.unstaged or ()),
            ("untracked", untracked),
        ):
            if items:
                dirty = True
                print(f"{label}: {sorted(set(items))[:20]}")
        if not dirty:
            print("worktree clean")
    elif cmd == "add":
        repo = porcelain.open_repo(root)
        paths = sys.argv[2:] if len(sys.argv) > 2 else ["."]
        porcelain.add(repo, paths)
        print("staged paths:", paths)
        status = porcelain.status(repo)
        print("staged:", sorted(status.staged.get("add", []))[:20])
    elif cmd == "rmcached":
        repo = porcelain.open_repo(root)
        idx = repo.open_index()
        for p in sys.argv[2:]:
            key = p.replace("\\", "/").encode("utf-8")
            if key in idx._byname:
                del idx._byname[key]
                print("removed from index:", p)
            else:
                print("not in index:", p)
        idx.write()
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
