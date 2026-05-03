#!/usr/bin/env python3

"""Minimal welcome script for a lightweight custom git-like entrypoint."""

import sys
from commands import add_paths, commit, init_repo, log_history, print_welcome, repo_status


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init":
            init_repo()
        elif cmd == "add":
            add_paths(sys.argv[2:])
        elif cmd == "commit":
            commit(sys.argv[2:])
        elif cmd == "status":
            repo_status()
        elif cmd == "log":
            log_history()
        else:
            print(f"Unknown command: {cmd}")
            print("Available commands: init, add, commit, status, log")
    else:
        print_welcome()


if __name__ == "__main__":
    main()
