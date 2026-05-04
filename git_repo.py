"""Repository internals for the tiny git tool."""

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


def _replace_path(object_id):
    return os.path.join(_git_dir(), "replace", object_id)


def _read_replace(object_id):
    replace_path = _replace_path(object_id)
    if os.path.isfile(replace_path):
        with open(replace_path, "r", encoding="utf-8") as f:
            return f.read().strip() or None
    return None


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


def _tags_dir():
    return os.path.join(_git_dir(), "refs", "tags")


def _resolve_tag(target):
    if not target:
        return None
    tag_path = os.path.join(_tags_dir(), target)
    if os.path.isfile(tag_path):
        with open(tag_path, "r", encoding="utf-8") as tag_file:
            return tag_file.read().strip() or None
    return None


def _commit_parents(commit_id):
    data = _read_object(commit_id)
    if data is None:
        return []
    parents = []
    for line in data.decode("utf-8", errors="replace").splitlines():
        if line.startswith("parent "):
            parents.append(line.split(" ", 1)[1])
        elif line == "":
            break
    return parents


def _find_merge_base(a, b):
    if a == b:
        return a
    ancestors = {a}
    queue = [a]
    while queue:
        current = queue.pop(0)
        for parent in _commit_parents(current):
            if parent not in ancestors:
                ancestors.add(parent)
                queue.append(parent)

    queue = [b]
    visited = set()
    while queue:
        current = queue.pop(0)
        if current in ancestors:
            return current
        visited.add(current)
        for parent in _commit_parents(current):
            if parent not in visited:
                queue.append(parent)
    return None


def _restore_tree(tree):
    for path, oid in tree.items():
        if oid is None:
            if os.path.isfile(path):
                os.remove(path)
            continue
        data = _read_object(oid)
        if data is None:
            continue
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)


def _write_tree(tree):
    _write_index({k: v for k, v in tree.items() if v is not None})
    _restore_tree(tree)


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
            commit_id = ref_file.read().strip() or None
        if commit_id:
            replacement = _read_replace(commit_id)
            return replacement or commit_id
        return None

    if os.path.isfile(_object_path(target)):
        replacement = _read_replace(target)
        return replacement or target

    for filename in os.listdir(os.path.join(_git_dir(), "objects")):
        if filename.startswith(target):
            replacement = _read_replace(filename)
            return replacement or filename

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

    for root, dirs, files in os.walk(os.getcwd(), topdown=False):
        if ".git" in root.split(os.sep):
            continue
        for filename in files:
            path = _normalize_path(os.path.relpath(os.path.join(root, filename), os.getcwd()))
            if path in tracked and path not in tree:
                os.remove(path)
        if root != os.getcwd() and not os.listdir(root):
            os.rmdir(root)
