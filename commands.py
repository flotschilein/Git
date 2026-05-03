"""Simple command implementations for the tiny git tool."""

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
    return os.path.join(_git_dir(), "index")


def _object_path(object_id):
    return os.path.join(_git_dir(), "objects", object_id)


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


def print_welcome():
    project = os.path.basename(os.getcwd())
    print(f"Welcome to your tiny git tool for '{project}'!")
    print("Nothing important here — just a friendly hello.")
    print("Use 'init' to create a repo, 'add' to stage files, or 'status' to inspect the repo.")
