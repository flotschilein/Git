#!/usr/bin/env python3

"""Minimal welcome script for a lightweight custom git-like entrypoint."""

import sys
from commands import add_paths, am, apply, archive, blame, bisect, branch, bundle, checkout, cherry_pick, clean, commit, config, diff, describe, fsck, gc, grep, init_repo, instaweb, log_history, merge, mv, notes, print_welcome, prune, rebase, reflog, repo_status, reset, restore, rm, revert, show, stash, switch, tag, worktree
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
        elif cmd == "grep":
            grep(sys.argv[2:])
        elif cmd == "archive":
            archive(sys.argv[2:])
        elif cmd == "am":
            am(sys.argv[2:])
        elif cmd == "apply":
            apply(sys.argv[2:])
        elif cmd == "bundle":
            bundle(sys.argv[2:])
        elif cmd == "bisect":
            bisect(sys.argv[2:])
        elif cmd == "blame":
            blame(sys.argv[2:])
        elif cmd == "fsck":
            fsck(sys.argv[2:])
        elif cmd == "gc":
            gc(sys.argv[2:])
        elif cmd == "instaweb":
            instaweb(sys.argv[2:])
        elif cmd == "notes":
            notes(sys.argv[2:])
        elif cmd == "prune":
            prune(sys.argv[2:])
        elif cmd == "worktree":
            worktree(sys.argv[2:])
        elif cmd == "reflog":
            reflog(sys.argv[2:])
        elif cmd == "show":
            show(sys.argv[2:])
        elif cmd == "describe":
            describe(sys.argv[2:])
        elif cmd == "merge":
            merge(sys.argv[2:])
        elif cmd == "stash":
            stash(sys.argv[2:])
        elif cmd == "revert":
            revert(sys.argv[2:])
        elif cmd == "rebase":
            rebase(sys.argv[2:])
        elif cmd == "cherry-pick":
            cherry_pick(sys.argv[2:])
        elif cmd == "restore":
            restore(sys.argv[2:])
        elif cmd == "switch":
            switch(sys.argv[2:])
        elif cmd == "clean":
            clean(sys.argv[2:])
        elif cmd == "config":
            config(sys.argv[2:])
        elif cmd == "mv":
            mv(sys.argv[2:])
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
            print("Available commands: init, add, rm, tag, commit, branch, checkout, switch, restore, rebase, cherry-pick, describe, grep, archive, am, apply, bundle, bisect, worktree, blame, fsck, gc, instaweb, notes, prune, reflog, reset, merge, stash, revert, clean, config, mv, status, log, diff, show, clone, push, pull, fetch, remote")
    else:
        print_welcome()


if __name__ == "__main__":
    main()
