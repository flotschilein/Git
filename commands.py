"""Simple command implementations for the tiny git tool."""

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

    print(f"Initialized empty Git repository in {git_dir}")


def repo_status():
    git_dir = os.path.join(os.getcwd(), ".git")
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

    untracked_files = []
    for root, dirs, files in os.walk(os.getcwd()):
        if ".git" in root.split(os.sep):
            continue
        for filename in files:
            path = os.path.relpath(os.path.join(root, filename), os.getcwd())
            untracked_files.append(path)

    if not untracked_files:
        print("nothing to commit, working tree clean")
    else:
        print("Untracked files:")
        for path in sorted(untracked_files):
            print(f"  {path}")


def print_welcome():
    project = os.path.basename(os.getcwd())
    print(f"Welcome to your tiny git tool for '{project}'!")
    print("Nothing important here — just a friendly hello.")
    print("Use 'init' to create a repo in the current directory.")
