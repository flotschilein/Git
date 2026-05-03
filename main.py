#!/usr/bin/env python3

"""Minimal welcome script for a lightweight custom git-like entrypoint."""

import sys
from commands import init_repo, print_welcome, repo_status


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init":
            init_repo()
        elif cmd == "status":
            repo_status()
        else:
            print(f"Unknown command: {cmd}")
            print("Available commands: init, status")
    else:
        print_welcome()


if __name__ == "__main__":
    main()
