#!/usr/bin/env python3

"""Minimal welcome script for a lightweight custom git-like entrypoint."""

import sys
from commands import add_paths, branch, checkout, commit, diff, init_repo, log_history, merge, print_welcome, repo_status, reset, rm, show, tag
from network_cmds import clone, push, pull, fetch, remote


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "init":
            init_repo()
        elif cmd == "add":
            add_paths(sys.argv[2:])
        elif cmd == "rm":
            rm(sys.argv[2:])
        elif cmd == "tag":
            tag(sys.argv[2:])
        elif cmd == "commit":
            commit(sys.argv[2:])
        elif cmd == "branch":
            branch(sys.argv[2:])
        elif cmd == "checkout":
            checkout(sys.argv[2:])
        elif cmd == "reset":
            reset(sys.argv[2:])
        elif cmd == "status":
            repo_status()
        elif cmd == "log":
            log_history()
        elif cmd == "diff":
            diff(sys.argv[2:])
        elif cmd == "show":
            show(sys.argv[2:])
        elif cmd == "merge":
            merge(sys.argv[2:])
        elif cmd == "clone":
            clone(sys.argv[2:])
        elif cmd == "push":
            push(sys.argv[2:])
        elif cmd == "pull":
            pull(sys.argv[2:])
        elif cmd == "fetch":
            fetch(sys.argv[2:])
        elif cmd == "remote":
            remote(sys.argv[2:])
        else:
            print(f"Unknown command: {cmd}")
            print("Available commands: init, add, rm, tag, commit, branch, checkout, reset, merge, status, log, diff, show, clone, push, pull, fetch, remote")
    else:
        print_welcome()


if __name__ == "__main__":
    main()
