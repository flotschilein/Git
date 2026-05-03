"""Simple command implementations for the tiny git tool."""

import difflib
import hashlib
import os


def init_repo():
    git_dir = os.path.join(os.getcwd(), ".git")
    if os.path.exists(git_dir):
        print("Reinitialized existing Git repository in .git")
        return

    os.makedirs(git_dir, exist_ok=True)
    with open(os.path.join(git_dir, "HEAD"), "w", encoding="utf-8") as head_file:
        head_file.write("ref: refs/heads/main\n")

    os.makedirs(os.path.join(git_dir, "refs", "heads"), exist_ok=True)
    os.makedirs(os.path.join(git_dir, "objects"), exist_ok=True)
    os.makedirs(os.path.join(git_dir, "info"), exist_ok=True)

    print(f"Initialized empty Git repository in {git_dir}")


def _git_dir():
    return os.path.join(os.getcwd(), ".git")


def _index_path():
    return os.path.join(_git_dir(), "tinygit_index")


def _object_path(object_id):
    return os.path.join(_git_dir(), "objects", object_id)


def _read_head():
    head_path = os.path.join(_git_dir(), "HEAD")
    if not os.path.isfile(head_path):
        return None
    with open(head_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _current_branch():
    head = _read_head()
    if head and head.startswith("ref: "):
        return head.split("/")[-1]
    return None


def _current_commit_id():
    head = _read_head()
    if not head:
        return None
    if head.startswith("ref: "):
        ref_path = os.path.join(_git_dir(), head[5:])
        if os.path.isfile(ref_path):
            with open(ref_path, "r", encoding="utf-8") as f:
                return f.read().strip() or None
        return None
    return head


def _write_head(commit_id):
    head = _read_head()
    if head and head.startswith("ref: "):
        ref_path = os.path.join(_git_dir(), head[5:])
        os.makedirs(os.path.dirname(ref_path), exist_ok=True)
        with open(ref_path, "w", encoding="utf-8") as ref_file:
            ref_file.write(commit_id + "\n")
    else:
        with open(os.path.join(_git_dir(), "HEAD"), "w", encoding="utf-8") as head_file:
            head_file.write(commit_id + "\n")


def _read_object(object_id):
    object_path = _object_path(object_id)
    if not os.path.isfile(object_path):
        return None
    with open(object_path, "rb") as obj_file:
        return obj_file.read()


def _normalize_path(path):
    return os.path.normpath(path).lstrip("./")


def _read_index():
    index_path = _index_path()
    if not os.path.isfile(index_path):
        return {}

    entries = {}
    with open(index_path, "r", encoding="utf-8") as index_file:
        for line in index_file:
            line = line.rstrip("\n")
            if not line:
                continue
            digest, path = line.split(" ", 1)
            entries[path] = digest
    return entries


def _write_index(entries):
    index_path = _index_path()
    with open(index_path, "w", encoding="utf-8") as index_file:
        for path in sorted(entries):
            index_file.write(f"{entries[path]} {path}\n")


def _hash_object(data):
    return hashlib.sha1(data).hexdigest()


def _store_object(data):
    object_id = _hash_object(data)
    object_path = _object_path(object_id)
    if not os.path.exists(object_path):
        with open(object_path, "wb") as obj_file:
            obj_file.write(data)
    return object_id


def _collect_files(path):
    if os.path.isfile(path):
        return [path]
    if os.path.isdir(path):
        collected = []
        for root, dirs, files in os.walk(path):
            if ".git" in root.split(os.sep):
                continue
            for filename in files:
                collected.append(os.path.join(root, filename))
        return collected
    raise FileNotFoundError(path)


def add_paths(paths):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not paths:
        print("usage: add <pathspec>...")
        return

    if paths == ["-A"] or paths == ["--all"]:
        paths = ["."]

    index = _read_index()
    staged = []

    for path in paths:
        normalized = _normalize_path(path)
        if normalized == "":
            normalized = "."

        try:
            files = _collect_files(normalized)
        except FileNotFoundError:
            print(f"fatal: pathspec '{path}' did not match any files")
            continue

        for filepath in sorted(files):
            relpath = os.path.relpath(filepath, os.getcwd())
            relpath = _normalize_path(relpath)
            if relpath.startswith(".git"):
                continue

            with open(filepath, "rb") as f:
                data = f.read()
            object_id = _store_object(data)
            index[relpath] = object_id
            staged.append(relpath)

    _write_index(index)

    if staged:
        print("added to staging area:")
        for path in sorted(staged):
            print(f"  {path}")
    else:
        print("nothing added to commit")


def commit(message_args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not message_args or message_args[0] != "-m" or len(message_args) == 1:
        print("usage: commit -m <message>")
        return

    message = " ".join(message_args[1:]).strip()
    if not message:
        print("usage: commit -m <message>")
        return

    index = _read_index()
    if not index:
        print("nothing to commit")
        return

    parent = _current_commit_id()
    contents = []
    if parent:
        contents.append(f"parent {parent}")
    for path in sorted(index):
        contents.append(f"{index[path]} {path}")
    contents.append("")
    contents.append(message)

    data = "\n".join(contents).encode("utf-8")
    commit_id = _store_object(data)
    _write_head(commit_id)

    branch = _current_branch() or "HEAD"
    print(f"[{branch} {commit_id[:7]}] {message}")


def log_history():
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    commit_id = _current_commit_id()
    if not commit_id:
        print("fatal: no commits yet")
        return

    while commit_id:
        data = _read_object(commit_id)
        if data is None:
            print(f"fatal: commit object {commit_id} not found")
            return
        text = data.decode("utf-8", errors="replace")
        lines = text.splitlines()
        parent = None
        message_lines = []
        reading_message = False
        for line in lines:
            if line == "":
                reading_message = True
                continue
            if reading_message:
                message_lines.append(line)
            elif line.startswith("parent "):
                parent = line.split(" ", 1)[1]

        print(f"commit {commit_id}")
        if message_lines:
            for msg_line in message_lines:
                print(f"    {msg_line}")
        else:
            print("    (no commit message)")
        print()

        commit_id = parent


def branch(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    refs_dir = os.path.join(git_dir, "refs", "heads")
    os.makedirs(refs_dir, exist_ok=True)

    current = _current_branch()
    if not args:
        branches = []
        for root, dirs, files in os.walk(refs_dir):
            for filename in files:
                branch_name = os.path.relpath(os.path.join(root, filename), refs_dir)
                branches.append(branch_name)
        for branch_name in sorted(branches):
            prefix = "* " if branch_name == current else "  "
            print(prefix + branch_name)
        return

    name = args[0]
    commit_id = _current_commit_id()
    if not commit_id:
        print("fatal: cannot create branch with no commits yet")
        return

    branch_path = os.path.join(refs_dir, name)
    if os.path.exists(branch_path):
        print(f"fatal: branch '{name}' already exists")
        return

    os.makedirs(os.path.dirname(branch_path), exist_ok=True)
    with open(branch_path, "w", encoding="utf-8") as ref_file:
        ref_file.write(commit_id + "\n")
    print(f"Created branch {name} at {commit_id[:7]}")


def _tags_dir():
    return os.path.join(_git_dir(), "refs", "tags")


def tag(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    tags_dir = _tags_dir()
    os.makedirs(tags_dir, exist_ok=True)

    if not args:
        tags = []
        for root, dirs, files in os.walk(tags_dir):
            for filename in files:
                tag_name = os.path.relpath(os.path.join(root, filename), tags_dir)
                tags.append(tag_name)
        for tag_name in sorted(tags):
            print(tag_name)
        return

    name = args[0]
    target = None
    if len(args) > 1:
        target = args[1]

    commit_id = _resolve_commit(target)
    if not commit_id:
        print(f"fatal: ambiguous argument '{target}'")
        return

    tag_path = os.path.join(tags_dir, name)
    if os.path.exists(tag_path):
        print(f"fatal: tag '{name}' already exists")
        return

    os.makedirs(os.path.dirname(tag_path), exist_ok=True)
    with open(tag_path, "w", encoding="utf-8") as tag_file:
        tag_file.write(commit_id + "\n")
    print(f"Created tag {name} at {commit_id[:7]}")


def _resolve_tag(target):
    if not target:
        return None
    tag_path = os.path.join(_tags_dir(), target)
    if os.path.isfile(tag_path):
        with open(tag_path, "r", encoding="utf-8") as tag_file:
            return tag_file.read().strip() or None
    return None


def show(args):
    if not args:
        print("usage: show <object> | <ref>")
        return

    name = args[0]
    commit_id = _resolve_tag(name) or _resolve_commit(name)
    if not commit_id:
        print(f"fatal: ambiguous argument '{name}'")
        return

    data = _read_object(commit_id)
    if data is None:
        print(f"fatal: object {commit_id} not found")
        return

    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if lines and (lines[0].startswith("parent ") or any(" " in line for line in lines if line and not line.startswith("parent "))):
        print(f"commit {commit_id}")
        for line in lines:
            if line == "":
                print()
            else:
                print(line)
        return

    print(text)


def _commit_tree(commit_id):
    data = _read_object(commit_id)
    if data is None:
        return {}
    lines = data.decode("utf-8", errors="replace").splitlines()
    tree = {}
    for line in lines:
        if line == "":
            break
        if line.startswith("parent "):
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2:
            oid, path = parts
            tree[path] = oid
    return tree


def _restore_commit(commit_id):
    tree = _commit_tree(commit_id)
    for path, oid in tree.items():
        data = _read_object(oid)
        if data is None:
            continue
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)


def _resolve_commit(target):
    if not target:
        return _current_commit_id()

    refs_path = os.path.join(_git_dir(), "refs", "heads", target)
    if os.path.isfile(refs_path):
        with open(refs_path, "r", encoding="utf-8") as ref_file:
            return ref_file.read().strip() or None

    if os.path.isfile(_object_path(target)):
        return target

    # allow abbreviated object IDs when unambiguous
    for filename in os.listdir(os.path.join(_git_dir(), "objects")):
        if filename.startswith(target):
            return filename

    return None


def _write_index_from_tree(commit_id):
    tree = _commit_tree(commit_id)
    _write_index(tree)
    return tree


def _hard_reset_commit(commit_id):
    tree = _commit_tree(commit_id)
    index = _read_index()
    tracked = set(index.keys())

    _restore_commit(commit_id)
    _write_index(tree)

    # remove previously tracked files no longer present in target commit
    for root, dirs, files in os.walk(os.getcwd(), topdown=False):
        if ".git" in root.split(os.sep):
            continue
        for filename in files:
            path = _normalize_path(os.path.relpath(os.path.join(root, filename), os.getcwd()))
            if path in tracked and path not in tree:
                os.remove(path)
        if root != os.getcwd() and not os.listdir(root):
            os.rmdir(root)


def reset(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    mode = "mixed"
    target = None
    if args and args[0] in ("--soft", "--mixed", "--hard"):
        mode = args[0][2:]
        args = args[1:]

    if args:
        target = args[0]

    commit_id = _resolve_commit(target)
    if not commit_id:
        print(f"fatal: ambiguous argument '{target}'")
        return

    if mode == "soft":
        _write_head(commit_id)
        print(f"Reset HEAD to {commit_id[:7]} (soft)")
        return

    if mode == "mixed":
        _write_head(commit_id)
        _write_index_from_tree(commit_id)
        print(f"Reset HEAD to {commit_id[:7]} and updated index (mixed)")
        return

    if mode == "hard":
        _write_head(commit_id)
        _hard_reset_commit(commit_id)
        print(f"Reset HEAD to {commit_id[:7]} and updated index and working tree (hard)")
        return


def checkout(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        print("usage: checkout <branch>")
        return

    name = args[0]
    ref_path = os.path.join(git_dir, "refs", "heads", name)
    if not os.path.isfile(ref_path):
        print(f"fatal: invalid reference: {name}")
        return

    with open(ref_path, "r", encoding="utf-8") as ref_file:
        commit_id = ref_file.read().strip()

    if not commit_id:
        print(f"fatal: branch '{name}' has no commits")
        return

    with open(os.path.join(git_dir, "HEAD"), "w", encoding="utf-8") as head_file:
        head_file.write(f"ref: refs/heads/{name}\n")

    _restore_commit(commit_id)
    print(f"Switched to branch '{name}'")


def repo_status():
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    head_path = os.path.join(git_dir, "HEAD")
    branch = "unknown"
    if os.path.isfile(head_path):
        with open(head_path, "r", encoding="utf-8") as head_file:
            ref = head_file.read().strip()
        if ref.startswith("ref:"):
            branch = ref.split("/")[-1]
        else:
            branch = "detached HEAD"

    print(f"On branch {branch}")

    index = _read_index()
    staged = sorted(index.keys())

    untracked_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        if ".git" in root.split(os.sep):
            continue
        for filename in files:
            path = os.path.relpath(os.path.join(root, filename), os.getcwd())
            path = _normalize_path(path)
            if path in index:
                continue
            untracked_files.append(path)

    if staged:
        print("\nChanges to be committed:")
        for path in staged:
            print(f"  new file:   {path}")

    if untracked_files:
        print("\nUntracked files:")
        for path in sorted(untracked_files):
            print(f"  {path}")

    if not staged and not untracked_files:
        print("nothing to commit, working tree clean")


def rm(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        print("usage: rm <pathspec>...")
        return

    index = _read_index()
    removed = []
    for arg in args:
        normalized = _normalize_path(arg)
        if normalized == "":
            normalized = "."

        if os.path.isdir(normalized):
            for root, dirs, files in os.walk(normalized, topdown=False):
                if ".git" in root.split(os.sep):
                    continue
                for filename in files:
                    path = _normalize_path(os.path.relpath(os.path.join(root, filename), os.getcwd()))
                    if os.path.isfile(path):
                        os.remove(path)
                        removed.append(path)
                        index.pop(path, None)
                if not os.listdir(root):
                    os.rmdir(root)
        elif os.path.isfile(normalized):
            path = _normalize_path(os.path.relpath(normalized, os.getcwd()))
            os.remove(normalized)
            removed.append(path)
            index.pop(path, None)
        else:
            print(f"fatal: pathspec '{arg}' did not match any files")

    _write_index(index)
    if removed:
        for path in sorted(removed):
            print(f"removed {path}")

    return


def diff(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    index = _read_index()
    targets = []
    if not args:
        targets = sorted(index.keys())
    else:
        for arg in args:
            normalized = _normalize_path(arg)
            if normalized == "":
                normalized = "."
            if os.path.isfile(normalized):
                targets.append(_normalize_path(os.path.relpath(normalized, os.getcwd())))
            elif os.path.isdir(normalized):
                for root, dirs, files in os.walk(normalized):
                    if ".git" in root.split(os.sep):
                        continue
                    for filename in files:
                        targets.append(_normalize_path(os.path.relpath(os.path.join(root, filename), os.getcwd())))
            else:
                print(f"fatal: pathspec '{arg}' did not match any files")
        targets = sorted(set(targets))

    if not targets:
        print("nothing to diff")
        return

    any_diff = False
    for path in targets:
        old_lines = []
        if path in index:
            old_data = _read_object(index[path])
            if old_data is not None:
                old_lines = old_data.decode("utf-8", errors="replace").splitlines(True)

        new_lines = []
        if os.path.isfile(path):
            with open(path, "rb") as f:
                new_lines = f.read().decode("utf-8", errors="replace").splitlines(True)
        else:
            print(f"diff --git a/{path} b/{path}")
            print(f"deleted file mode 100644")
            any_diff = True
            continue

        if old_lines == new_lines:
            continue

        any_diff = True
        diff_lines = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            lineterm=""
        )
        for line in diff_lines:
            print(line)

    if not any_diff:
        return


def print_welcome():
    project = os.path.basename(os.getcwd())
    print(f"Welcome to your tiny git tool for '{project}'!")
    print("Nothing important here — just a friendly hello.")
    print("Use 'init' to create a repo, 'add' to stage files, 'rm' to remove paths, 'tag' to create or list tags, 'show' to inspect refs or objects, 'commit' to record changes, 'branch' to manage branches, 'checkout' and 'reset' to move around history, and 'status', 'log', or 'diff' to inspect the repo.")
