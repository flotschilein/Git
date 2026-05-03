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


def print_welcome():
    project = os.path.basename(os.getcwd())
    print(f"Welcome to your tiny git tool for '{project}'!")
    print("Nothing important here — just a friendly hello.")
    print("Use 'init' to create a repo in the current directory.")
