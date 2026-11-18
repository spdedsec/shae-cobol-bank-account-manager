# SHAE COBOL Bank Account Manager

<div align="center">

```
   ____  _   _    _    _____     ____    _    _     ____
  / ___|| | | |  / \  | ____|   / ___|  / \  | |   / ___|
  \___ \| |_| | / _ \ |  _|    | |     / _ \ | |  | |
   ___) |  _  |/ ___ \| |___   | |___ / ___ \| |__| |___
  |____/|_| |_/_/   \_\_____|   \____/_/   \_\_____\____|
```

**A COBOL-inspired terminal bank account manager in pure Python 3.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)
[![CLI](https://img.shields.io/badge/Type-CLI-orange.svg)](#)

</div>

---

## What is this?

The **SHAE COBOL Bank Account Manager** is a terminal-based accounts system
written in the spirit of COBOL's DATA DIVISION / PROCEDURE DIVISION structure,
implemented in pure Python 3 standard library. It supports:

- Account creation
- Deposits and withdrawals
- Balance queries
- Transaction history
- JSON persistence of all accounts (by default `~/.shae-bank-data.json`)

All monetary amounts use `Decimal` arithmetic to avoid floating-point rounding.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Commands](#commands)
4. [COBOL-Inspired Design](#cobol-inspired-design)
5. [Persistence](#persistence)
6. [Project Structure](#project-structure)
7. [Development](#development)
8. [License](#license)

## Installation

### Prerequisites

- Python 3.9 or newer
- A terminal that supports ANSI escape codes (optional)

### Install via CLI

```bash
git clone https://github.com/spdedsec/shae-cobol-bank-account-manager.git
cd shae-cobol-bank-account-manager
bash scripts/install.sh
```

The installer creates a wrapper at `~/.local/bin/shae-bank`. Ensure
`~/.local/bin` is on your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Add that line to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) to make it
permanent.

### Run directly without installing

```bash
python3 src/main.py
```

## Quick Start

```bash
shae-bank
```

```
 BANK > create Alice
 BANK > deposit <account-id> 100.00
 BANK > withdraw <account-id> 25.00
 BANK > balance <account-id>
 BANK > history <account-id>
 BANK > list
 BANK > quit
```

## Commands

| Command | Description |
|---------|-------------|
| `create <name>` | Open a new account |
| `deposit <account> <amount> [desc]` | Add funds |
| `withdraw <account> <amount> [desc]` | Remove funds |
| `balance <account>` | Show current balance |
| `history <account> [limit]` | Show transaction history |
| `list` | List all accounts |
| `help` / `?` | Show help |
| `quit` / `exit` | Exit |

**Account matching**: you can reference an account by full UUID, its first 8
characters (prefix), or its name (case-insensitive).

Aliases: `dep`, `credit`, `wd`, `debit`, `bal`, `show`, `hist`, `txns`, `ls`.

## COBOL-Inspired Design

The source mirrors classic COBOL structuring:

- **DATA DIVISION** — `Account` and `Transaction` dataclasses represent
  fixed-format records. Field comments use PIC clauses (e.g.
  `05 BALANCE PIC S9(12)V99 COMP-3`).
- **PROCEDURE DIVISION** — `Bank` class encapsulates operations.
- **FILE SECTION** — `BankStorage` handles sequential JSON persistence with
  atomic writes.
- **STOP RUN** — the main loop exits cleanly on `quit`.

## Persistence

Accounts are stored in a JSON file at `~/.shae-bank-data.json` by default. The
file is written atomically (temp file + rename) so a crash cannot leave a
half-written data file.

You can override the path by subclassing `BankStorage` or by editing
`DEFAULT_DATA_FILE` in `src/main.py`.

## Project Structure

```
shae-cobol-bank-account-manager/
├── src/
│   └── main.py              # Bank engine, data model, CLI
├── tests/
│   └── test_game.py         # Pytest test suite
├── scripts/
│   └── install.sh           # CLI install script
├── Makefile                 # Build / test / lint targets
├── pyproject.toml           # Python packaging metadata
├── README.md                # This file
├── DESIGN.md                # Design system notes
└── .github/
    └── workflows/
        └── release.yml      # GitHub release workflow
```

## Development

```bash
make test      # Run tests
make lint      # Lint
make clean     # Clean artifacts
```

## License

MIT License — see [LICENSE](LICENSE).

---

*Built with the SHAE Field Manual design system: warm paper, near-black ink,
oxide signal, flat and physical, motion is typesetting.*