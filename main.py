#!/usr/bin/env python3

"""Minimal welcome script for a lightweight custom git-like entrypoint."""

import sys
from commands import add_paths, am, apply, archive, blame, bisect, branch, bundle, checkout, cherry_pick, clean, commit, config, diff, describe, format_patch, fsck, gc, grep, init_repo, instaweb, log_history, merge, mergetool, mv, notes, print_welcome, prune, rebase, reflog, repo_status, request_pull, reset, restore, rm, revert, send_email, show, stash, switch, tag, version, help, worktree, ls_files, rev_parse, cat_file, shortlog, whatchanged, difftool, show_ref, for_each_ref, ls_tree, hash_object, count_objects, pack_refs, verify_tag, update_index, write_tree, commit_tree, rev_list, submodule, rerere, replace, filter_branch, sparse_checkout, fast_export, pack_objects, fast_import, maintenance, upload_pack, receive_pack, daemon, svn, cvsimport, gui, citool, repack, check_ignore
from network_cmds import clone, push, pull, fetch, remote


COMMANDS = [
    ("init", lambda args: init_repo()),
    ("add", add_paths),
    ("rm", rm),
    ("tag", tag),
    ("commit", commit),
    ("branch", branch),
    ("checkout", checkout),
    ("reset", reset),
    ("status", lambda args: repo_status()),
    ("log", lambda args: log_history()),
    ("diff", diff),
    ("grep", grep),
    ("archive", archive),
    ("am", am),
    ("apply", apply),
    ("bundle", bundle),
    ("bisect", bisect),
    ("blame", blame),
    ("format-patch", format_patch),
    ("request-pull", request_pull),
    ("send-email", send_email),
    ("fsck", fsck),
    ("gc", gc),
    ("instaweb", instaweb),
    ("notes", notes),
    ("prune", prune),
    ("worktree", worktree),
    ("reflog", reflog),
    ("show", show),
    ("describe", describe),
    ("merge", merge),
    ("ls-files", ls_files),
    ("rev-parse", rev_parse),
    ("cat-file", cat_file),
    ("shortlog", shortlog),
    ("whatchanged", whatchanged),
    ("difftool", difftool),
    ("show-ref", show_ref),
    ("for-each-ref", for_each_ref),
    ("ls-tree", ls_tree),
    ("hash-object", hash_object),
    ("count-objects", count_objects),
    ("pack-refs", pack_refs),
    ("verify-tag", verify_tag),
    ("update-index", update_index),
    ("write-tree", write_tree),
    ("commit-tree", commit_tree),
    ("rev-list", rev_list),
    ("submodule", submodule),
    ("rerere", rerere),
    ("replace", replace),
    ("filter-branch", filter_branch),
    ("sparse-checkout", sparse_checkout),
    ("fast-export", fast_export),
    ("fast-import", fast_import),
    ("maintenance", maintenance),
    ("upload-pack", upload_pack),
    ("receive-pack", receive_pack),
    ("daemon", daemon),
    ("svn", svn),
    ("cvsimport", cvsimport),
    ("gui", gui),
    ("citool", citool),
    ("repack", repack),
    ("check-ignore", check_ignore),
    ("pack-objects", pack_objects),
    ("stash", stash),
    ("revert", revert),
    ("rebase", rebase),
    ("mergetool", mergetool),
    ("help", help),
    ("version", version),
    ("cherry-pick", cherry_pick),
    ("restore", restore),
    ("switch", switch),
    ("clean", clean),
    ("config", config),
    ("mv", mv),
    ("clone", clone),
    ("push", push),
    ("pull", pull),
    ("fetch", fetch),
    ("remote", remote),
]

COMMAND_MAP = {name: handler for name, handler in COMMANDS}
AVAILABLE_COMMANDS = ", ".join(name for name, _ in COMMANDS)


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        handler = COMMAND_MAP.get(cmd)
        if handler:
            handler(sys.argv[2:])
        else:
            print(f"Unknown command: {cmd}")
            print(f"Available commands: {AVAILABLE_COMMANDS}")
    else:
        print_welcome()


if __name__ == "__main__":
    main()
