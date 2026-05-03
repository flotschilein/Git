#!/usr/bin/env python3

"""Minimal welcome script for a lightweight custom git-like entrypoint."""

import os


def main():
    project = os.path.basename(os.getcwd())
    print(f"Welcome to your tiny git tool for '{project}'!")
    print("Nothing important here — just a friendly hello.")


if __name__ == "__main__":
    main()
