#!/usr/bin/env python3

"""Minimal welcome script for a lightweight custom git-like entrypoint."""

import sys
from commands import init_repo, print_welcome


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_repo()
    else:
        print_welcome()


if __name__ == "__main__":
    main()
