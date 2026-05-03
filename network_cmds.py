import os
import shutil


def clone(args):
    if not args or len(args) > 2:
        print("usage: clone <repository> [directory]")
        return

    repository = args[0]
    destination = args[1] if len(args) == 2 else None

    if not os.path.isdir(repository):
        print(f"fatal: repository '{repository}' not found")
        return

    git_dir = os.path.join(repository, ".git")
    if not os.path.isdir(git_dir):
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
