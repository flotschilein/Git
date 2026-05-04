"""Simple command implementations for the tiny git tool."""

import difflib
import io
import os
import re
import shutil
import tarfile
import tempfile

from git_repo import (
    init_repo,
    _collect_files,
    _current_branch,
    _current_commit_id,
    _find_merge_base,
    _git_dir,
    _hash_object,
    _normalize_path,
    _object_path,
    _read_head,
    _read_index,
    _read_object,
    _resolve_commit,
    _resolve_tag,
    _restore_commit,
    _restore_tree,
    _store_object,
    _tags_dir,
    _write_head,
    _write_index,
    _write_index_from_tree,
    _write_tree,
    _hard_reset_commit,
    _commit_parents,
    _commit_tree,
)


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


def _config_path():
    return os.path.join(_git_dir(), "config")


def _read_config():
    config_path = _config_path()
    if not os.path.isfile(config_path):
        return {}

    config = {}
    with open(config_path, "r", encoding="utf-8") as config_file:
        for line in config_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
    return config


def _write_config(config):
    config_path = _config_path()
    with open(config_path, "w", encoding="utf-8") as config_file:
        for key in sorted(config):
            config_file.write(f"{key} = {config[key]}\n")


def config(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        print("usage: config --list | --get <key> | --set <key> <value> | --unset <key>")
        return

    action = args[0]
    cfg = _read_config()

    if action == "--list":
        for key in sorted(cfg):
            print(f"{key} = {cfg[key]}")
        return

    if action == "--get":
        if len(args) != 2:
            print("usage: config --get <key>")
            return
        key = args[1]
        if key in cfg:
            print(cfg[key])
        return

    if action == "--set":
        if len(args) < 3:
            print("usage: config --set <key> <value>")
            return
        key = args[1]
        value = " ".join(args[2:])
        cfg[key] = value
        _write_config(cfg)
        return

    if action == "--unset":
        if len(args) != 2:
            print("usage: config --unset <key>")
            return
        key = args[1]
        if key in cfg:
            del cfg[key]
            _write_config(cfg)
        return

    print("usage: config --list | --get <key> | --set <key> <value> | --unset <key>")


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

    delete_mode = None
    if args[0] in ("-d", "-D", "--delete"):
        if args[0] == "-D":
            delete_mode = "forced"
            args = args[1:]
        elif args[0] == "--delete":
            args = args[1:]
            if args and args[0] in ("-f", "--force"):
                delete_mode = "forced"
                args = args[1:]
        else:
            delete_mode = "normal"
            args = args[1:]

        if len(args) != 1:
            print("usage: branch -d <branch> | branch -D <branch> | branch --delete <branch> | branch --delete -f <branch>")
            return

        name = args[0]
        branch_path = os.path.join(refs_dir, name)
        if not os.path.isfile(branch_path):
            print(f"fatal: branch '{name}' not found")
            return

        if current == name:
            current_commit = _current_commit_id() or "unknown"
            print(f"fatal: Cannot delete branch '{name}' checked out at {current_commit[:7]}")
            return

        os.remove(branch_path)
        parent_dir = os.path.dirname(branch_path)
        while parent_dir and parent_dir != refs_dir and parent_dir.startswith(refs_dir):
            if os.listdir(parent_dir):
                break
            os.rmdir(parent_dir)
            parent_dir = os.path.dirname(parent_dir)

        if delete_mode == "forced":
            print(f"Deleted branch {name} (forced)")
        else:
            print(f"Deleted branch {name}")
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

    if args[0] in ("-d", "--delete"):
        if len(args) != 2:
            print("usage: tag -d <tag> | tag --delete <tag>")
            return
        name = args[1]
        tag_path = os.path.join(tags_dir, name)
        if not os.path.isfile(tag_path):
            print(f"fatal: tag '{name}' not found")
            return
        os.remove(tag_path)
        parent_dir = os.path.dirname(tag_path)
        while parent_dir and parent_dir != tags_dir and parent_dir.startswith(tags_dir):
            if os.listdir(parent_dir):
                break
            os.rmdir(parent_dir)
            parent_dir = os.path.dirname(parent_dir)
        print(f"Deleted tag {name}")
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


def describe(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if len(args) > 1:
        print("usage: describe [<commit>]")
        return

    target = args[0] if args else None
    commit_id = _resolve_tag(target) or _resolve_commit(target)
    if not commit_id:
        print(f"fatal: ambiguous argument '{target}'")
        return

    matches = []
    refs_root = os.path.join(git_dir, "refs")
    for root, dirs, files in os.walk(refs_root):
        for filename in files:
            ref_path = os.path.join(root, filename)
            with open(ref_path, "r", encoding="utf-8") as ref_file:
                ref_value = ref_file.read().strip()
            if ref_value == commit_id:
                ref_name = os.path.relpath(ref_path, refs_root)
                matches.append(ref_name)

    if matches:
        matches.sort()
        print(matches[0])
    else:
        print(commit_id[:7])


def merge(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        print("usage: merge <branch>")
        return

    target = args[0]
    target_commit = _resolve_tag(target) or _resolve_commit(target)
    if not target_commit:
        print(f"fatal: ambiguous argument '{target}'")
        return

    current_commit = _current_commit_id()
    if not current_commit:
        print("fatal: cannot merge without a current commit")
        return

    if current_commit == target_commit:
        print("Already up to date.")
        return

    base_commit = _find_merge_base(current_commit, target_commit)
    if base_commit == target_commit:
        print("Already up to date.")
        return

    if base_commit == current_commit:
        _write_head(target_commit)
        _write_index_from_tree(target_commit)
        _restore_commit(target_commit)
        print(f"Fast-forwarded to {target}")
        return

    base_tree = _commit_tree(base_commit)
    our_tree = _commit_tree(current_commit)
    their_tree = _commit_tree(target_commit)

    merged_tree = {}
    conflicts = []
    paths = sorted(set(base_tree) | set(our_tree) | set(their_tree))
    for path in paths:
        base_oid = base_tree.get(path)
        our_oid = our_tree.get(path)
        their_oid = their_tree.get(path)

        if our_oid == their_oid:
            merged_tree[path] = our_oid
            continue

        if our_oid == base_oid:
            merged_tree[path] = their_oid
            continue

        if their_oid == base_oid:
            merged_tree[path] = our_oid
            continue

        if our_oid is None:
            merged_tree[path] = their_oid
            continue

        if their_oid is None:
            merged_tree[path] = our_oid
            continue

        if our_oid and their_oid:
            our_text = _read_object(our_oid).decode("utf-8", errors="replace").splitlines(True)
            their_text = _read_object(their_oid).decode("utf-8", errors="replace").splitlines(True)
            merged = []
            merged.append("<<<<<<< OURS\n")
            merged.extend(our_text)
            if our_text and not our_text[-1].endswith("\n"):
                merged.append("\n")
            merged.append("=======\n")
            merged.extend(their_text)
            if their_text and not their_text[-1].endswith("\n"):
                merged.append("\n")
            merged.append(">>>>>>> THEIRS\n")
            merged_content = "".join(merged).encode("utf-8")
            merged_oid = _store_object(merged_content)
            with open(path, "wb") as f:
                f.write(merged_content)
            merged_tree[path] = merged_oid
            conflicts.append(path)
            continue

        merged_tree[path] = our_oid or their_oid

    _write_tree(merged_tree)
    if conflicts:
        print("Automatic merge failed; fix conflicts and commit the result.")
        for path in conflicts:
            print(f"CONFLICT (content): Merge conflict in {path}")
        return

    parents = [current_commit, target_commit]
    contents = [f"parent {p}" for p in parents]
    for path in sorted(merged_tree):
        oid = merged_tree[path]
        if oid is not None:
            contents.append(f"{oid} {path}")
    contents.append("")
    contents.append(f"Merge branch '{target}'")

    commit_data = "\n".join(contents).encode("utf-8")
    commit_id = _store_object(commit_data)
    _write_head(commit_id)
    _write_index({k: v for k, v in merged_tree.items() if v is not None})
    print(f"Merge made by the simple merge strategy.\n[{commit_id[:7]}] Merge branch '{target}'")


def stash(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        print("usage: stash save [<message>] | stash list | stash pop | stash drop")
        return

    subcommand = args[0]
    stash_ref = os.path.join(git_dir, "refs", "stash")

    if subcommand == "save":
        message = " ".join(args[1:]).strip() or "WIP"
        files = []
        for root, dirs, filenames in os.walk(os.getcwd()):
            if ".git" in root.split(os.sep):
                continue
            for filename in filenames:
                files.append(os.path.join(root, filename))

        contents = []
        previous_stash = None
        if os.path.isfile(stash_ref):
            with open(stash_ref, "r", encoding="utf-8") as stash_file:
                previous_stash = stash_file.read().strip() or None
        if previous_stash:
            contents.append(f"parent {previous_stash}")

        for filepath in sorted(files):
            relpath = _normalize_path(os.path.relpath(filepath, os.getcwd()))
            with open(filepath, "rb") as f:
                data = f.read()
            oid = _store_object(data)
            contents.append(f"{oid} {relpath}")

        contents.append("")
        contents.append(f"stash@{{0}}: WIP on {_current_branch() or 'HEAD'}: {message}")
        stash_commit = _store_object("\n".join(contents).encode("utf-8"))
        os.makedirs(os.path.dirname(stash_ref), exist_ok=True)
        with open(stash_ref, "w", encoding="utf-8") as stash_file:
            stash_file.write(stash_commit + "\n")
        print(f"Saved working directory and index state WIP on {_current_branch() or 'HEAD'}: {message}")
        return

    if subcommand == "list":
        if not os.path.isfile(stash_ref):
            return

        commit_id = open(stash_ref, "r", encoding="utf-8").read().strip()
        index = 0
        while commit_id:
            print(f"stash@{{{index}}}: {commit_id[:7]}")
            parents = _commit_parents(commit_id)
            commit_id = parents[0] if parents else None
            index += 1
        return

    if subcommand == "pop":
        if not os.path.isfile(stash_ref):
            print("No stash entries found.")
            return

        with open(stash_ref, "r", encoding="utf-8") as stash_file:
            commit_id = stash_file.read().strip()
        if not commit_id:
            print("No stash entries found.")
            return

        stash_tree = _commit_tree(commit_id)
        _restore_tree(stash_tree)
        _write_index_from_tree(commit_id)

        for root, dirs, files in os.walk(os.getcwd(), topdown=False):
            if ".git" in root.split(os.sep):
                continue
            for filename in files:
                path = _normalize_path(os.path.relpath(os.path.join(root, filename), os.getcwd()))
                if path not in stash_tree:
                    os.remove(os.path.join(root, filename))
            if root != os.getcwd() and not os.listdir(root):
                os.rmdir(root)

        parents = _commit_parents(commit_id)
        next_stash = parents[0] if parents else None
        if next_stash:
            with open(stash_ref, "w", encoding="utf-8") as stash_file:
                stash_file.write(next_stash + "\n")
        else:
            os.remove(stash_ref)

        print(f"Popped stash {commit_id[:7]}")
        return

    if subcommand == "apply":
        if not os.path.isfile(stash_ref):
            print("No stash entries found.")
            return

        with open(stash_ref, "r", encoding="utf-8") as stash_file:
            commit_id = stash_file.read().strip()
        if not commit_id:
            print("No stash entries found.")
            return

        stash_tree = _commit_tree(commit_id)
        _restore_tree(stash_tree)
        _write_index_from_tree(commit_id)

        print(f"Applied stash {commit_id[:7]}")
        return

    if subcommand == "drop":
        if not os.path.isfile(stash_ref):
            print("No stash entries found.")
            return

        with open(stash_ref, "r", encoding="utf-8") as stash_file:
            commit_id = stash_file.read().strip()
        if not commit_id:
            print("No stash entries found.")
            return

        parents = _commit_parents(commit_id)
        next_stash = parents[0] if parents else None
        if next_stash:
            with open(stash_ref, "w", encoding="utf-8") as stash_file:
                stash_file.write(next_stash + "\n")
        else:
            os.remove(stash_ref)

        print(f"Dropped stash {commit_id[:7]}")
        return

    print("usage: stash save [<message>] | stash list | stash pop | stash apply | stash drop")


def revert(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if len(args) != 1:
        print("usage: revert <commit>")
        return

    target = args[0]
    target_commit = _resolve_tag(target) or _resolve_commit(target)
    if not target_commit:
        print(f"fatal: ambiguous argument '{target}'")
        return

    current_commit = _current_commit_id()
    if not current_commit:
        print("fatal: no commits yet")
        return

    parent_commits = _commit_parents(target_commit)
    base_commit = parent_commits[0] if parent_commits else None
    base_tree = _commit_tree(base_commit) if base_commit else {}
    target_tree = _commit_tree(target_commit)
    current_tree = _commit_tree(current_commit)

    revert_tree = dict(current_tree)
    for path in sorted(set(base_tree) | set(target_tree)):
        base_oid = base_tree.get(path)
        target_oid = target_tree.get(path)

        if base_oid == target_oid:
            continue

        if base_oid is None and target_oid is not None:
            revert_tree.pop(path, None)
            continue

        revert_tree[path] = base_oid

    for path in sorted(set(current_tree) - set(revert_tree)):
        if os.path.isfile(path):
            os.remove(path)

    _write_tree(revert_tree)

    message_lines = []
    commit_text = _read_object(target_commit).decode("utf-8", errors="replace").splitlines()
    reading_message = False
    for line in commit_text:
        if reading_message:
            message_lines.append(line)
        elif line == "":
            reading_message = True

    reverted_message = message_lines[0] if message_lines else target_commit
    revert_message = f"Revert \"{reverted_message}\""

    contents = [f"parent {current_commit}"]
    for path in sorted(revert_tree):
        oid = revert_tree[path]
        if oid is not None:
            contents.append(f"{oid} {path}")
    contents.append("")
    contents.append(revert_message)

    commit_data = "\n".join(contents).encode("utf-8")
    commit_id = _store_object(commit_data)
    _write_head(commit_id)
    print(f"[{_current_branch() or 'HEAD'} {commit_id[:7]}] {revert_message}")


def cherry_pick(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if len(args) != 1:
        print("usage: cherry-pick <commit>")
        return

    target = args[0]
    target_commit = _resolve_tag(target) or _resolve_commit(target)
    if not target_commit:
        print(f"fatal: ambiguous argument '{target}'")
        return

    current_commit = _current_commit_id()
    if not current_commit:
        print("fatal: no commits yet")
        return

    data = _read_object(target_commit)
    if data is None:
        print(f"fatal: commit object {target_commit} not found")
        return

    lines = data.decode("utf-8", errors="replace").splitlines()
    tree_lines = []
    message_lines = []
    reading_message = False
    for line in lines:
        if line == "":
            reading_message = True
            continue
        if reading_message:
            message_lines.append(line)
        elif not line.startswith("parent "):
            tree_lines.append(line)

    commit_message = "\n".join(message_lines)
    contents = [f"parent {current_commit}"]
    contents.extend(tree_lines)
    contents.append("")
    if commit_message:
        contents.append(commit_message)

    new_commit_id = _store_object("\n".join(contents).encode("utf-8"))
    _write_head(new_commit_id)
    _write_index_from_tree(new_commit_id)
    _restore_commit(new_commit_id)
    print(f"[{_current_branch() or 'HEAD'} {new_commit_id[:7]}] cherry-picked {target_commit[:7]}")


def clean(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    force = False
    dry_run = False
    remove_dirs = False
    if not args:
        print("usage: clean -f [-d] | clean -n [-d]")
        return

    for arg in args:
        if arg == "-f":
            force = True
        elif arg == "-n":
            dry_run = True
        elif arg == "-d":
            remove_dirs = True
        else:
            print("usage: clean -f [-d] | clean -n [-d]")
            return

    if not force and not dry_run:
        print("usage: clean -f [-d] | clean -n [-d]")
        return

    index = _read_index()
    tracked = set(index.keys())
    untracked_files = []

    for root, dirs, files in os.walk(os.getcwd()):
        if ".git" in root.split(os.sep):
            dirs[:] = []
            continue
        for filename in files:
            path = _normalize_path(os.path.relpath(os.path.join(root, filename), os.getcwd()))
            if path not in tracked:
                untracked_files.append(path)

    untracked_files.sort()
    removed_dirs = []

    if dry_run:
        for path in untracked_files:
            print(f"Would remove {path}")
        if remove_dirs:
            for root, dirs, files in os.walk(os.getcwd(), topdown=False):
                if ".git" in root.split(os.sep):
                    continue
                if not os.listdir(root) and root != os.getcwd():
                    removed_dirs.append(_normalize_path(os.path.relpath(root, os.getcwd())))
            for path in sorted(removed_dirs):
                print(f"Would remove directory {path}")
        return

    for path in untracked_files:
        os.remove(path)
        print(f"removed {path}")

    if remove_dirs:
        for root, dirs, files in os.walk(os.getcwd(), topdown=False):
            if ".git" in root.split(os.sep):
                continue
            if not os.listdir(root) and root != os.getcwd():
                try:
                    os.rmdir(root)
                    removed_dirs.append(_normalize_path(os.path.relpath(root, os.getcwd())))
                except OSError:
                    pass
        for path in sorted(removed_dirs):
            print(f"removed {path}")

    if not untracked_files and not removed_dirs:
        return


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


def switch(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        print("usage: switch <branch> | switch -c <branch>")
        return

    if args[0] == "-c":
        if len(args) != 2:
            print("usage: switch -c <branch>")
            return

        name = args[1]
        commit_id = _current_commit_id()
        if not commit_id:
            print("fatal: cannot create branch with no commits yet")
            return

        refs_dir = os.path.join(git_dir, "refs", "heads")
        branch_path = os.path.join(refs_dir, name)
        if os.path.exists(branch_path):
            print(f"fatal: branch '{name}' already exists")
            return

        os.makedirs(os.path.dirname(branch_path), exist_ok=True)
        with open(branch_path, "w", encoding="utf-8") as ref_file:
            ref_file.write(commit_id + "\n")

        with open(os.path.join(git_dir, "HEAD"), "w", encoding="utf-8") as head_file:
            head_file.write(f"ref: refs/heads/{name}\n")

        _restore_commit(commit_id)
        print(f"Switched to a new branch '{name}'")
        return

    checkout(args)


def restore(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        print("usage: restore [--source <commit>] <pathspec>...")
        return

    source_commit = None
    pathspecs = args
    if args[0] == "--source":
        if len(args) < 3:
            print("usage: restore [--source <commit>] <pathspec>...")
            return

        source_commit = _resolve_tag(args[1]) or _resolve_commit(args[1])
        if not source_commit:
            print(f"fatal: ambiguous argument '{args[1]}'")
            return

        pathspecs = args[2:]
        tree = _commit_tree(source_commit)
    else:
        tree = _read_index()
        if not tree:
            print("fatal: your current index is empty")
            return

    restored = []
    for arg in pathspecs:
        normalized = _normalize_path(arg)
        if normalized == "":
            normalized = "."

        matched = False
        if normalized == ".":
            for path, oid in sorted(tree.items()):
                if oid is None:
                    continue
                data = _read_object(oid)
                if data is None:
                    continue
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(data)
                restored.append(path)
            matched = bool(restored)
        elif normalized in tree:
            oid = tree[normalized]
            data = _read_object(oid)
            if data is not None:
                os.makedirs(os.path.dirname(normalized), exist_ok=True)
                with open(normalized, "wb") as f:
                    f.write(data)
                restored.append(normalized)
            matched = True
        else:
            prefix = normalized + os.sep
            for path, oid in sorted(tree.items()):
                if path == normalized or path.startswith(prefix):
                    if oid is None:
                        continue
                    data = _read_object(oid)
                    if data is None:
                        continue
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "wb") as f:
                        f.write(data)
                    restored.append(path)
                    matched = True

        if not matched:
            print(f"fatal: pathspec '{arg}' did not match any files")

    for path in sorted(set(restored)):
        print(f"restored {path}")


def rebase(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if len(args) != 1:
        print("usage: rebase <branch>")
        return

    target = args[0]
    target_commit = _resolve_tag(target) or _resolve_commit(target)
    if not target_commit:
        print(f"fatal: ambiguous argument '{target}'")
        return

    current_commit = _current_commit_id()
    if not current_commit:
        print("fatal: no commits yet")
        return

    if current_commit == target_commit:
        print("Already up to date.")
        return

    base_commit = _find_merge_base(current_commit, target_commit)
    if base_commit == target_commit:
        print("Already up to date.")
        return

    if base_commit == current_commit:
        _write_head(target_commit)
        _write_index_from_tree(target_commit)
        _restore_commit(target_commit)
        print(f"Fast-forwarded to {target}")
        return

    commits = []
    commit_id = current_commit
    while commit_id and commit_id != base_commit:
        commits.append(commit_id)
        parents = _commit_parents(commit_id)
        commit_id = parents[0] if parents else None

    commits.reverse()
    new_parent = target_commit
    for old_commit in commits:
        data = _read_object(old_commit)
        if data is None:
            print(f"fatal: commit object {old_commit} not found")
            return

        lines = data.decode("utf-8", errors="replace").splitlines()
        tree_lines = []
        message_lines = []
        reading_message = False
        for line in lines:
            if line == "":
                reading_message = True
                continue
            if reading_message:
                message_lines.append(line)
            elif not line.startswith("parent "):
                tree_lines.append(line)

        contents = [f"parent {new_parent}"]
        contents.extend(tree_lines)
        contents.append("")
        contents.extend(message_lines)
        new_parent = _store_object("\n".join(contents).encode("utf-8"))

    _write_head(new_parent)
    _write_index_from_tree(new_parent)
    _restore_commit(new_parent)
    print(f"Rebased current branch onto {target}")


def grep(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        print("usage: grep <pattern> [<path>...]")
        return

    pattern = args[0]
    paths = args[1:] if len(args) > 1 else ["."]
    matches = []

    for path in paths:
        normalized = _normalize_path(path)
        if normalized == "":
            normalized = "."

        if os.path.isdir(normalized):
            for root, dirs, files in os.walk(normalized):
                if ".git" in root.split(os.sep):
                    continue
                for filename in files:
                    filepath = os.path.join(root, filename)
                    if os.path.isfile(filepath):
                        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                            for line_num, line in enumerate(f, start=1):
                                if pattern in line:
                                    matches.append(f"{_normalize_path(os.path.relpath(filepath, os.getcwd()))}:{line_num}:{line.rstrip()}")
        elif os.path.isfile(normalized):
            with open(normalized, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, start=1):
                    if pattern in line:
                        matches.append(f"{normalized}:{line_num}:{line.rstrip()}")
        else:
            print(f"fatal: pathspec '{path}' did not match any files or directories")

    for match in matches:
        print(match)


def reflog(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if args:
        print("usage: reflog")
        return

    commit_id = _current_commit_id()
    if not commit_id:
        print("fatal: no commits yet")
        return

    index = 0
    while commit_id:
        data = _read_object(commit_id)
        if data is None:
            print(f"fatal: commit object {commit_id} not found")
            return
        lines = data.decode("utf-8", errors="replace").splitlines()
        message = ""
        for line in lines:
            if line == "":
                continue
            if not line.startswith("parent "):
                message = line
                break
        print(f"HEAD@{{{index}}}: {commit_id[:7]} {message}")
        parents = _commit_parents(commit_id)
        commit_id = parents[0] if parents else None
        index += 1


def blame(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if len(args) != 1:
        print("usage: blame <file>")
        return

    path = _normalize_path(args[0])
    if not os.path.isfile(path):
        print(f"fatal: pathspec '{args[0]}' did not match any files")
        return

    commit_id = _current_commit_id()
    if not commit_id:
        print("fatal: no commits yet")
        return

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    for lineno, line in enumerate(lines, start=1):
        print(f"{commit_id[:7]} ({lineno:4}) {line.rstrip()}")


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


def mv(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args or len(args) < 2:
        print("usage: mv <source>... <destination>")
        return

    src_paths = [arg for arg in args[:-1]]
    dst = args[-1]
    index = _read_index()
    moved = []

    if len(src_paths) > 1:
        if not os.path.isdir(dst):
            print("fatal: destination is not a directory")
            return

    for src in src_paths:
        src_normalized = _normalize_path(src)
        src_path = src if os.path.isabs(src) else src_normalized
        if not os.path.exists(src_path):
            print(f"fatal: pathspec '{src}' did not match any files")
            continue

        if len(src_paths) > 1 or os.path.isdir(dst):
            destination_path = os.path.join(dst, os.path.basename(src_path))
        else:
            destination_path = dst

        if not os.path.isabs(destination_path):
            destination_path = _normalize_path(destination_path)

        destination_dir = os.path.dirname(destination_path)
        if destination_dir and not os.path.isdir(destination_dir):
            os.makedirs(destination_dir, exist_ok=True)

        try:
            shutil.move(src_path, destination_path)
        except Exception as exc:
            print(f"fatal: unable to move '{src}': {exc}")
            continue

        old_index_path = _normalize_path(os.path.relpath(src_path, os.getcwd()))
        new_index_path = _normalize_path(os.path.relpath(destination_path, os.getcwd()))
        if old_index_path in index:
            index[new_index_path] = index.pop(old_index_path)
        moved.append((old_index_path, new_index_path))

    if moved:
        _write_index(index)
        for old_path, new_path in moved:
            print(f"renamed {old_path} -> {new_path}")


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


def archive(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        print("usage: archive <file> [<commit>]")
        return

    archive_path = args[0]
    target = args[1] if len(args) > 1 else None

    if target:
        commit_id = _resolve_tag(target) or _resolve_commit(target)
        if not commit_id:
            print(f"fatal: ambiguous argument '{target}'")
            return
        tree = _commit_tree(commit_id)
        items = [(path, _read_object(oid)) for path, oid in sorted(tree.items()) if oid is not None]
    else:
        items = []
        for root, dirs, files in os.walk(os.getcwd()):
            if ".git" in root.split(os.sep):
                continue
            for filename in files:
                filepath = os.path.join(root, filename)
                relpath = _normalize_path(os.path.relpath(filepath, os.getcwd()))
                with open(filepath, "rb") as f:
                    items.append((relpath, f.read()))

    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            for relpath, data in items:
                tarinfo = tarfile.TarInfo(name=relpath)
                tarinfo.size = len(data)
                tarinfo.mtime = int(os.path.getmtime(os.path.join(os.getcwd(), relpath))) if not target else 0
                tarinfo.mode = 0o644
                tar.addfile(tarinfo, fileobj=io.BytesIO(data))
        print(f"created archive {archive_path}")
    except Exception as exc:
        print(f"fatal: could not create archive: {exc}")


def _collect_bundle_objects(commit_id, collected):
    if commit_id in collected:
        return
    data = _read_object(commit_id)
    if data is None:
        return
    collected.add(commit_id)

    lines = data.decode("utf-8", errors="replace").splitlines()
    for line in lines:
        if line.startswith("parent "):
            _collect_bundle_objects(line.split(" ", 1)[1], collected)
        elif line == "":
            break
        elif " " in line:
            oid, _ = line.split(" ", 1)
            _collect_bundle_objects(oid, collected)


def bundle(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args or args[0] not in ("create", "list"):
        print("usage: bundle create <file> <commit>... | bundle list <file>")
        return

    action = args[0]
    if action == "list":
        if len(args) != 2:
            print("usage: bundle list <file>")
            return
        bundle_path = args[1]
        if not os.path.isfile(bundle_path):
            print(f"fatal: bundle '{bundle_path}' not found")
            return
        try:
            with tarfile.open(bundle_path, "r:gz") as tar:
                try:
                    member = tar.getmember("bundle-commits.txt")
                    f = tar.extractfile(member)
                    if f:
                        for line in f.read().decode("utf-8").splitlines():
                            print(line)
                except KeyError:
                    print("fatal: invalid bundle")
        except Exception as exc:
            print(f"fatal: could not read bundle: {exc}")
        return

    if action == "create":
        if len(args) < 3:
            print("usage: bundle create <file> <commit>...")
            return

        bundle_path = args[1]
        commit_ids = []
        for target in args[2:]:
            commit_id = _resolve_tag(target) or _resolve_commit(target)
            if not commit_id:
                print(f"fatal: ambiguous argument '{target}'")
                return
            commit_ids.append(commit_id)

        object_ids = set()
        for commit_id in commit_ids:
            _collect_bundle_objects(commit_id, object_ids)

        try:
            with tarfile.open(bundle_path, "w:gz") as tar:
                commit_data = "\n".join(commit_ids).encode("utf-8")
                info = tarfile.TarInfo(name="bundle-commits.txt")
                info.size = len(commit_data)
                tar.addfile(info, fileobj=io.BytesIO(commit_data))
                for oid in sorted(object_ids):
                    obj_data = _read_object(oid)
                    if obj_data is None:
                        continue
                    info = tarfile.TarInfo(name=os.path.join("objects", oid))
                    info.size = len(obj_data)
                    tar.addfile(info, fileobj=io.BytesIO(obj_data))
            print(f"created bundle {bundle_path}")
        except Exception as exc:
            print(f"fatal: could not create bundle: {exc}")


def _bisect_dir():
    return os.path.join(_git_dir(), "bisect")


def _bisect_state_path():
    return os.path.join(_bisect_dir(), "state")


def _read_bisect_state():
    path = _bisect_state_path()
    if not os.path.isfile(path):
        return None
    state = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            key, _, value = line.partition("=")
            state[key.strip()] = value.strip()
    return state


def _write_bisect_state(state):
    os.makedirs(_bisect_dir(), exist_ok=True)
    with open(_bisect_state_path(), "w", encoding="utf-8") as f:
        for key in sorted(state):
            f.write(f"{key}={state[key]}\n")


def _bisect_path(bad, good):
    if bad == good:
        return [bad]
    path = [bad]
    current = bad
    while current != good:
        parents = _commit_parents(current)
        if not parents:
            return []
        current = parents[0]
        path.append(current)
        if len(path) > 10000:
            break
    return path if current == good else []


def _detach_head(commit_id):
    with open(os.path.join(_git_dir(), "HEAD"), "w", encoding="utf-8") as head_file:
        head_file.write(commit_id + "\n")


def apply(args):
    if len(args) != 1:
        print("usage: apply <patch-file>")
        return

    patch_file = args[0]
    if not os.path.isfile(patch_file):
        print(f"fatal: patch file '{patch_file}' not found")
        return

    files = []
    current_path = None
    hunks = []
    with open(patch_file, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("diff --git"):
                if current_path and hunks:
                    files.append((current_path, hunks))
                current_path = None
                hunks = []
                continue
            if line.startswith("+++ "):
                path = line[4:].strip()
                if path.startswith("b/"):
                    current_path = _normalize_path(path[2:])
                elif path == "/dev/null":
                    current_path = None
                continue
            if line.startswith("@@"):
                match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
                if not match:
                    continue
                old_start = int(match.group(1))
                old_count = int(match.group(2) or "1")
                hunks.append({
                    "old_start": old_start,
                    "old_count": old_count,
                    "lines": [],
                })
                continue
            if current_path and hunks and line[0] in {" ", "+", "-", "\\"}:
                hunks[-1]["lines"].append(line)

    if current_path and hunks:
        files.append((current_path, hunks))

    if not files:
        print("fatal: no patch content")
        return

    for path, file_hunks in files:
        orig_lines = []
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                orig_lines = f.readlines()

        result = []
        src_index = 0
        for hunk in file_hunks:
            start = hunk["old_start"] - 1
            result.extend(orig_lines[src_index:start])
            index = start
            for patch_line in hunk["lines"]:
                tag = patch_line[0]
                content = patch_line[1:]
                if tag == " ":
                    if index >= len(orig_lines) or orig_lines[index].rstrip("\n") != content.rstrip("\n"):
                        print(f"fatal: patch failed at {path}")
                        return
                    result.append(orig_lines[index])
                    index += 1
                elif tag == "-":
                    if index >= len(orig_lines) or orig_lines[index].rstrip("\n") != content.rstrip("\n"):
                        print(f"fatal: patch failed at {path}")
                        return
                    index += 1
                elif tag == "+":
                    result.append(content)
            src_index = start + hunk["old_count"]
        result.extend(orig_lines[src_index:])

        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.writelines(result)
        print(f"Applied patch to {path}")


def am(args):
    if len(args) != 1:
        print("usage: am <mbox-file>")
        return

    mbox_path = args[0]
    if not os.path.isfile(mbox_path):
        print(f"fatal: patch file '{mbox_path}' not found")
        return

    with open(mbox_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    patches = []
    current = []
    for line in lines:
        if line.startswith("From ") and current:
            patches.append("".join(current))
            current = []
            continue
        current.append(line)
    if current:
        patches.append("".join(current))

    if not patches:
        print("fatal: no patch content")
        return

    for idx, patch_text in enumerate(patches, start=1):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
            tmp.write(patch_text)
            tmp_path = tmp.name
        try:
            apply([tmp_path])
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        print(f"Applied patch {idx} from mbox")


def bisect(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args:
        print("usage: bisect start <bad> <good> | bisect good | bisect bad | bisect reset")
        return

    subcommand = args[0]
    if subcommand == "start":
        if len(args) != 3:
            print("usage: bisect start <bad> <good>")
            return

        bad = _resolve_tag(args[1]) or _resolve_commit(args[1])
        good = _resolve_tag(args[2]) or _resolve_commit(args[2])
        if not bad or not good:
            print(f"fatal: ambiguous argument '{args[1] if not bad else args[2]}'")
            return

        base = _find_merge_base(bad, good)
        if base != good:
            print("fatal: good commit is not an ancestor of bad commit")
            return

        path = _bisect_path(bad, good)
        if len(path) <= 2:
            print("bisect: no intermediate commits to test")
            return

        midpoint = path[len(path) // 2]
        original_head = _read_head() or ""
        _write_bisect_state({
            "good": good,
            "bad": bad,
            "current": midpoint,
            "original_head": original_head,
        })
        _detach_head(midpoint)
        _restore_commit(midpoint)
        print(f"bisect started, testing {midpoint[:7]}")
        return

    if subcommand in ("good", "bad"):
        state = _read_bisect_state()
        if not state:
            print("fatal: no bisect in progress")
            return

        current = state["current"]
        state[subcommand] = current

        path = _bisect_path(state["bad"], state["good"])
        if len(path) <= 2:
            print(f"bisect complete: first bad commit is {current[:7]}")
            return

        midpoint = path[len(path) // 2]
        state["current"] = midpoint
        _write_bisect_state(state)
        _detach_head(midpoint)
        _restore_commit(midpoint)
        print(f"bisect next commit {midpoint[:7]}")
        return

    if subcommand == "reset":
        state = _read_bisect_state()
        if not state:
            print("fatal: no bisect in progress")
            return

        with open(os.path.join(git_dir, "HEAD"), "w", encoding="utf-8") as head_file:
            head_file.write(state["original_head"] + "\n")
        os.remove(_bisect_state_path())
        print("bisect reset")
        return

    print("usage: bisect start <bad> <good> | bisect good | bisect bad | bisect reset")


def worktree(args):
    git_dir = _git_dir()
    if not os.path.isdir(git_dir):
        print("fatal: not a git repository (or any of the parent directories): .git")
        return

    if not args or args[0] not in ("add", "list"):
        print("usage: worktree add <path> [<branch>] | worktree list")
        return

    subcommand = args[0]
    if subcommand == "list":
        worktrees_dir = os.path.join(git_dir, "worktrees")
        if not os.path.isdir(worktrees_dir):
            return
        for root, dirs, files in os.walk(worktrees_dir):
            for filename in files:
                print(filename)
        return

    if subcommand == "add":
        if len(args) not in (2, 3):
            print("usage: worktree add <path> [<branch>]")
            return

        destination = args[1]
        branch = args[2] if len(args) == 3 else _current_branch() or "main"
        branch_ref = os.path.join(git_dir, "refs", "heads", branch)
        if not os.path.isfile(branch_ref):
            print(f"fatal: branch '{branch}' not found")
            return

        if os.path.exists(destination):
            print(f"fatal: destination path '{destination}' already exists")
            return

        shutil.copytree(os.getcwd(), destination)
        with open(os.path.join(destination, ".git", "HEAD"), "w", encoding="utf-8") as head_file:
            head_file.write(f"ref: refs/heads/{branch}\n")

        worktrees_dir = os.path.join(git_dir, "worktrees")
        os.makedirs(worktrees_dir, exist_ok=True)
        worktree_name = os.path.basename(os.path.abspath(destination))
        with open(os.path.join(worktrees_dir, worktree_name), "w", encoding="utf-8") as worktree_file:
            worktree_file.write(os.path.abspath(destination) + "\n")

        print(f"Added worktree {destination} for branch {branch}")
        return


def print_welcome():
    project = os.path.basename(os.getcwd())
    print(f"Welcome to your tiny git tool for '{project}'!")
    print("Nothing important here — just a friendly hello.")
    print("Use 'init' to create a repo, 'add' to stage files, 'rm' to remove paths, 'tag' to create or list tags, 'show' to inspect refs or objects, 'commit' to record changes, 'branch' to manage branches, 'checkout' and 'switch' to move around history, 'restore' to recover files, 'reset' to move HEAD, 'merge' to combine branches, and 'status', 'log', or 'diff' to inspect the repo.")
