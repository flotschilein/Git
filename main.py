#!/usr/bin/env python3

"""Minimal welcome script for a lightweight custom git-like entrypoint."""

import sys
from commands import add_paths, am, apply, archive, blame, bisect, branch, bundle, checkout, cherry_pick, clean, commit, config, diff, describe, format_patch, fsck, gc, grep, init_repo, instaweb, log_history, merge, mergetool, mv, notes, print_welcome, prune, rebase, reflog, repo_status, request_pull, reset, restore, rm, revert, send_email, show, stash, switch, tag, version, help, worktree, ls_files, rev_parse, cat_file, shortlog, whatchanged, difftool, show_ref, for_each_ref, ls_tree, hash_object, count_objects, pack_refs, verify_tag, update_index, write_tree, commit_tree, rev_list, submodule, rerere, replace, filter_branch, sparse_checkout, fast_export, pack_objects
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
        elif cmd == "format-patch":
            format_patch(sys.argv[2:])
        elif cmd == "request-pull":
            request_pull(sys.argv[2:])
        elif cmd == "send-email":
            send_email(sys.argv[2:])
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
        elif cmd == "ls-files":
            ls_files(sys.argv[2:])
        elif cmd == "rev-parse":
            rev_parse(sys.argv[2:])
        elif cmd == "cat-file":
            cat_file(sys.argv[2:])
        elif cmd == "shortlog":
            shortlog(sys.argv[2:])
        elif cmd == "whatchanged":
            whatchanged(sys.argv[2:])
        elif cmd == "difftool":
            difftool(sys.argv[2:])
        elif cmd == "show-ref":
            show_ref(sys.argv[2:])
        elif cmd == "for-each-ref":
            for_each_ref(sys.argv[2:])
        elif cmd == "ls-tree":
            ls_tree(sys.argv[2:])
        elif cmd == "hash-object":
            hash_object(sys.argv[2:])
        elif cmd == "count-objects":
            count_objects(sys.argv[2:])
        elif cmd == "pack-refs":
            pack_refs(sys.argv[2:])
        elif cmd == "verify-tag":
            verify_tag(sys.argv[2:])
        elif cmd == "update-index":
            update_index(sys.argv[2:])
        elif cmd == "write-tree":
            write_tree(sys.argv[2:])
        elif cmd == "commit-tree":
            commit_tree(sys.argv[2:])
        elif cmd == "rev-list":
            rev_list(sys.argv[2:])
        elif cmd == "submodule":
            submodule(sys.argv[2:])
        elif cmd == "rerere":
            rerere(sys.argv[2:])
        elif cmd == "replace":
            replace(sys.argv[2:])
        elif cmd == "filter-branch":
            filter_branch(sys.argv[2:])
        elif cmd == "sparse-checkout":
            sparse_checkout(sys.argv[2:])
        elif cmd == "fast-export":
            fast_export(sys.argv[2:])
        elif cmd == "pack-objects":
            pack_objects(sys.argv[2:])
        elif cmd == "stash":
            stash(sys.argv[2:])
        elif cmd == "revert":
            revert(sys.argv[2:])
        elif cmd == "rebase":
            rebase(sys.argv[2:])
        elif cmd == "mergetool":
            mergetool(sys.argv[2:])
        elif cmd == "help":
            help(sys.argv[2:])
        elif cmd == "version":
            version(sys.argv[2:])
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
            print("Available commands: init, add, rm, tag, commit, branch, checkout, switch, restore, rebase, cherry-pick, describe, grep, archive, am, apply, bundle, bisect, worktree, blame, format-patch, request-pull, send-email, fsck, gc, instaweb, notes, prune, reflog, reset, merge, mergetool, ls-files, rev-parse, cat-file, shortlog, whatchanged, difftool, show-ref, for-each-ref, ls-tree, hash-object, count-objects, pack-refs, verify-tag, update-index, write-tree, commit-tree, rev-list, submodule, rerere, replace, filter-branch, sparse-checkout, fast-export, pack-objects, stash, revert, clean, config, mv, status, log, diff, show, clone, push, pull, fetch, remote, help, version")
    else:
        print_welcome()


if __name__ == "__main__":
    main()
