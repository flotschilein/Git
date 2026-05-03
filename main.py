#!/usr/bin/env python3

"""Minimal welcome script for a lightweight custom git-like entrypoint."""

import sys
from commands import add_paths, init_repo, print_welcome, repo_status


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init":
            init_repo()
        elif cmd == "add":
            add_paths(sys.argv[2:])
        elif cmd == "status":
            repo_status()
        else:
            print(f"Unknown command: {cmd}")
            print("Available commands: init, add, status")
    else:
        print_welcome()


if __name__ == "__main__":
    main()
