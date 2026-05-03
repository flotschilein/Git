import os
import shutil

from git_repo import _current_branch, _current_commit_id


def _git_dir(repo_root):
    return os.path.join(repo_root, ".git")


def _ref_path(repo_root, branch):
    return os.path.join(_git_dir(repo_root), "refs", "heads", branch)


def _is_git_repo(repo_root):
    return os.path.isdir(_git_dir(repo_root))


def _read_ref(repo_root, branch):
    ref_path = _ref_path(repo_root, branch)
    if os.path.isfile(ref_path):
        with open(ref_path, "r", encoding="utf-8") as ref_file:
            return ref_file.read().strip() or None
    return None


def _write_ref(repo_root, branch, commit_id):
    ref_path = _ref_path(repo_root, branch)
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, "w", encoding="utf-8") as ref_file:
        ref_file.write(commit_id + "\n")


def _remotes_dir(repo_root):
    path = os.path.join(_git_dir(repo_root), "remotes")
    os.makedirs(path, exist_ok=True)
    return path


def _remote_target_path(repo_root, remote_name):
    return os.path.join(_remotes_dir(repo_root), remote_name)


def _read_remote_target(repo_root, remote_name):
    target_path = _remote_target_path(repo_root, remote_name)
    if os.path.isfile(target_path):
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read().strip() or None
    return None


def _write_remote_target(repo_root, remote_name, target):
    target_path = _remote_target_path(repo_root, remote_name)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(target + "\n")


def _remove_remote_target(repo_root, remote_name):
    target_path = _remote_target_path(repo_root, remote_name)
    if os.path.isfile(target_path):
        os.remove(target_path)


def _list_remote_targets(repo_root):
    remote_targets = {}
    for filename in sorted(os.listdir(_remotes_dir(repo_root))):
        path = _remote_target_path(repo_root, filename)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                remote_targets[filename] = f.read().strip() or ""
    return remote_targets


def _resolve_remote_target(repo_root, repository):
    if os.path.isdir(repository) and _is_git_repo(repository):
        return repository, os.path.basename(os.path.normpath(repository))

    remote_target = _read_remote_target(repo_root, repository)
    if not remote_target:
        return None, None

    if not os.path.isdir(remote_target) or not _is_git_repo(remote_target):
        return None, None

    return remote_target, repository


def _remote_ref_path(repo_root, remote_name, branch):
    return os.path.join(_git_dir(repo_root), "refs", "remotes", remote_name, branch)


def _read_remote_ref(repo_root, remote_name, branch):
    ref_path = _remote_ref_path(repo_root, remote_name, branch)
    if os.path.isfile(ref_path):
        with open(ref_path, "r", encoding="utf-8") as ref_file:
            return ref_file.read().strip() or None
    return None


def _write_remote_ref(repo_root, remote_name, branch, commit_id):
    ref_path = _remote_ref_path(repo_root, remote_name, branch)
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, "w", encoding="utf-8") as ref_file:
        ref_file.write(commit_id + "\n")


def _commit_parents(repo_root, commit_id):
    object_path = os.path.join(_git_dir(repo_root), "objects", commit_id)
    if not os.path.isfile(object_path):
        return []
    with open(object_path, "rb") as object_file:
        data = object_file.read()
    text = data.decode("utf-8", errors="replace")
    parents = []
    for line in text.splitlines():
        if line.startswith("parent "):
            parents.append(line.split(" ", 1)[1])
        elif line == "":
            break
    return parents


def _is_ancestor(repo_root, ancestor, descendant):
    if ancestor == descendant:
        return True

    visited = set()
    queue = [descendant]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        if current == ancestor:
            return True
        for parent in _commit_parents(repo_root, current):
            if parent not in visited:
                queue.append(parent)
    return False


def _copy_objects(src_root, dst_root):
    src_objects = os.path.join(_git_dir(src_root), "objects")
    dst_objects = os.path.join(_git_dir(dst_root), "objects")
    os.makedirs(dst_objects, exist_ok=True)

    for root, dirs, files in os.walk(src_objects):
        rel_dir = os.path.relpath(root, src_objects)
        if rel_dir == ".":
            rel_dir = ""
        dest_dir = os.path.join(dst_objects, rel_dir)
        os.makedirs(dest_dir, exist_ok=True)
        for filename in files:
            src_path = os.path.join(root, filename)
            dst_path = os.path.join(dest_dir, filename)
            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)


def clone(args):
    if not args or len(args) > 2:
        print("usage: clone <repository> [directory]")
        return

    repository = args[0]
    destination = args[1] if len(args) == 2 else None

    if not os.path.isdir(repository):
        print(f"fatal: repository '{repository}' not found")
        return

    if not _is_git_repo(repository):
        print(f"fatal: repository '{repository}' is not a git repository")
        return

    if destination is None:
        destination = os.path.basename(os.path.abspath(repository))
        if destination.endswith(".git"):
            destination = destination[:-4]
        if not destination:
            destination = "clone"

    if os.path.exists(destination):
        print(f"fatal: destination path '{destination}' already exists and is not an empty directory")
        return

    try:
        shutil.copytree(repository, destination)
        print(f"Cloned repository into '{destination}'")
    except Exception as exc:
        print(f"fatal: clone failed: {exc}")


def push(args):
    if not args or len(args) > 2:
        print("usage: push <repository> [branch]")
        return

    repository = args[0]
    branch = args[1] if len(args) == 2 else _current_branch()

    if not branch:
        print("fatal: no branch specified and no current branch")
        return

    local_root = os.getcwd()
    if not _is_git_repo(local_root):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    remote_root, remote_name = _resolve_remote_target(local_root, repository)
    if not remote_root:
        print(f"fatal: repository or remote '{repository}' not found")
        return

    local_commit = _read_ref(local_root, branch)
    if local_commit is None:
        print(f"fatal: branch '{branch}' not found locally")
        return

    remote_commit = _read_ref(remote_root, branch)
    if remote_commit and not _is_ancestor(local_root, remote_commit, local_commit):
        print("fatal: non-fast-forward update")
        return

    _copy_objects(local_root, remote_root)
    _write_ref(remote_root, branch, local_commit)
    print(f"Pushed branch '{branch}' to '{repository}'")


def pull(args):
    if not args or len(args) > 2:
        print("usage: pull <repository> [branch]")
        return

    repository = args[0]
    branch = args[1] if len(args) == 2 else _current_branch()

    if not branch:
        print("fatal: no branch specified and no current branch")
        return

    local_root = os.getcwd()
    if not _is_git_repo(local_root):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    remote_root, remote_name = _resolve_remote_target(local_root, repository)
    if not remote_root:
        print(f"fatal: repository or remote '{repository}' not found")
        return

    local_commit = _read_ref(local_root, branch)
    if local_commit is None:
        print(f"fatal: branch '{branch}' not found locally")
        return

    remote_commit = _read_ref(remote_root, branch)
    if remote_commit is None:
        print(f"fatal: branch '{branch}' not found on remote")
        return

    if local_commit == remote_commit:
        print("Already up to date.")
        return

    if _is_ancestor(remote_root, local_commit, remote_commit):
        _copy_objects(remote_root, local_root)
        _write_ref(local_root, branch, remote_commit)
        print(f"Fast-forwarded branch '{branch}' to {remote_commit[:7]}")
        return

    print("fatal: merge required but pull only supports fast-forward updates")


def fetch(args):
    if not args or len(args) > 2:
        print("usage: fetch <repository> [branch]")
        return

    repository = args[0]
    branch = args[1] if len(args) == 2 else _current_branch()

    if not branch:
        print("fatal: no branch specified and no current branch")
        return

    local_root = os.getcwd()
    if not _is_git_repo(local_root):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    remote_root, remote_name = _resolve_remote_target(local_root, repository)
    if not remote_root:
        print(f"fatal: repository or remote '{repository}' not found")
        return

    remote_commit = _read_ref(remote_root, branch)
    if remote_commit is None:
        print(f"fatal: branch '{branch}' not found on remote")
        return

    if remote_name is None:
        remote_name = os.path.basename(os.path.normpath(remote_root))
    if remote_name.endswith(".git"):
        remote_name = remote_name[:-4]
    if not remote_name:
        remote_name = "remote"

    existing_remote_commit = _read_remote_ref(local_root, remote_name, branch)
    if existing_remote_commit == remote_commit:
        print("Already up to date.")
        return

    _copy_objects(remote_root, local_root)
    _write_remote_ref(local_root, remote_name, branch, remote_commit)
    print(f"Fetched branch '{branch}' from '{repository}'")


def remote(args):
    local_root = os.getcwd()
    if not _is_git_repo(local_root):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        for name in sorted(_list_remote_targets(local_root)):
            print(name)
        return

    subcommand = args[0]
    if subcommand == "-v":
        remotes = _list_remote_targets(local_root)
        for name, target in remotes.items():
            print(f"{name}\t{target}")
        return

    if subcommand == "add":
        if len(args) != 3:
            print("usage: remote add <name> <repository>")
            return
        name = args[1]
        repository = args[2]
        if _read_remote_target(local_root, name):
            print(f"fatal: remote {name} already exists")
            return
        target_path = os.path.abspath(repository)
        if not os.path.isdir(target_path) or not _is_git_repo(target_path):
            print(f"fatal: repository '{repository}' not found or is not a git repository")
            return
        _write_remote_target(local_root, name, target_path)
        print(f"Added remote {name} ({target_path})")
        return

    if subcommand in ("remove", "rm"):
        if len(args) != 2:
            print("usage: remote remove <name>")
            return
        name = args[1]
        if not _read_remote_target(local_root, name):
            print(f"fatal: remote {name} not found")
            return
        _remove_remote_target(local_root, name)
        print(f"Removed remote {name}")
        return

    if subcommand == "show" and len(args) == 2:
        name = args[1]
        target = _read_remote_target(local_root, name)
        if not target:
            print(f"fatal: remote {name} not found")
            return
        print(f"{name}\t{target}")
        return

    print("usage: remote [<args>]\n       remote [-v]\n       remote add <name> <repository>\n       remote remove <name>\n       remote show <name>")
