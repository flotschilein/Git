# Minimal Git-like Tool

A small, educational Git-like tool implemented in Python. This repository contains a lightweight implementation of several Git commands and plumbing useful for learning and experimentation — not a production replacement for Git.

## Overview

- Language: Python
- Purpose: Educational / experimental implementation of selected Git commands and repository primitives.

## Requirements

- Python 3.8+

## Quick start

1. From the project root (where `main.py` is located), run:

```bash
python3 main.py
```

This prints available commands. To run a specific command:

```bash
python3 main.py <command> [args]
```

Example:

```bash
python3 main.py commit
```

Some commands require an existing repository directory (a `.git`-like directory). The implementation is minimal and may print fatal errors when used outside an initialized repository.

## Common commands

This project implements many Git-like command names (porcelain and plumbing). Run `python3 main.py` to see the exact list.

## Contributing

Contributions and improvements are welcome. This is an educational project — please open issues or PRs with small, focused changes.

## License

MIT License — see `LICENSE` (not included). Feel free to add a LICENSE file if you intend to publish.


Enjoy exploring the code!