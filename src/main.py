#!/usr/bin/env python3
# ========================================================================
# SHAE COBOL Bank Account Manager
# Copyright (c) 2026 spdedsec <legendsatya7272@gmail.com>
# License: MIT
#
# A COBOL-inspired terminal bank account manager using DATA DIVISION-style
# records, written in pure Python 3 standard library. Account creation,
# deposit, withdraw, balance, transaction history, persisted to JSON file.
# ========================================================================

from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Design system constants (SHAE field-manual aesthetic applied to terminal)
# ---------------------------------------------------------------------------
_SUPPORTS_COLOR = sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"
_COLOUR_SCHEME: Dict[str, str] = {}

if _SUPPORTS_COLOR:
    _COLOUR_SCHEME = {
        "ink": "38;5;16",
        "paper": "48;5;230",
        "oxide": "38;5;124",
        "muted": "38;5;245",
        "ok": "38;5;22",
        "err": "38;5;124",
        "bold": "1",
        "reset": "0",
    }


def c(text: str, *styles: str) -> str:
    if not _SUPPORTS_COLOR or not _COLOUR_SCHEME:
        return text
    codes = ";".join(_COLOUR_SCHEME.get(s, "") for s in styles if s in _COLOUR_SCHEME)
    if not codes:
        return text
    return f"\x1b[{codes}m{text}\x1b[0m"


def hr(char: str = "-", width: int = 72) -> str:
    return char * width


def panel(title: str, body: str, width: int = 72) -> str:
    top = f"\u250c{hr(chr(0x2500), width - 2)}\u2510"
    bottom = f"\u2514{hr(chr(0x2500), width - 2)}\u2518"
    label = f"\u2502 {c(title, 'bold', 'oxide')} "
    label += " " * (width - 2 - len(title) - 2)
    label += "\u2502"
    body_lines = body.splitlines() or [""]
    rendered = [top, label]
    for line in body_lines:
        rendered.append(f"\u2502 {line:<{width - 4}} \u2502")
    rendered.append(bottom)
    return "\n".join(rendered)


# ---------------------------------------------------------------------------
# Data model (COBOL-inspired DATA DIVISION)
# ---------------------------------------------------------------------------


class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    INTEREST = "INTEREST"
    FEE = "FEE"


@dataclass
class Transaction:
    """PROCEDURE DIVISION — Transaction Record"""
    id: str
    type: TransactionType
    amount: Decimal
    balance_after: Decimal
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "amount": str(self.amount),
            "balance_after": str(self.balance_after),
            "timestamp": self.timestamp,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(
            id=data["id"],
            type=TransactionType(data["type"]),
            amount=Decimal(data["amount"]),
            balance_after=Decimal(data["balance_after"]),
            timestamp=data["timestamp"],
            description=data.get("description", ""),
        )


@dataclass
class Account:
    """DATA DIVISION — Account Record"""
    # 01 ACCOUNT-RECORD.
    #    05 ACCOUNT-ID         PIC X(36).
    #    05 ACCOUNT-NAME       PIC X(40).
    #    05 OPEN-DATE          PIC X(26).
    #    05 BALANCE            PIC S9(12)V99 COMP-3.
    #    05 STATUS             PIC X(10) VALUE "ACTIVE".
    id: str
    name: str
    open_date: str
    balance: Decimal = field(default_factory=lambda: Decimal("0.00"))
    status: str = "ACTIVE"
    transactions: List[Transaction] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "open_date": self.open_date,
            "balance": str(self.balance),
            "status": self.status,
            "transactions": [t.to_dict() for t in self.transactions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        return cls(
            id=data["id"],
            name=data["name"],
            open_date=data["open_date"],
            balance=Decimal(data["balance"]),
            status=data["status"],
            transactions=[Transaction.from_dict(t) for t in data.get("transactions", [])],
        )

    def add_transaction(self, txn: Transaction) -> None:
        self.transactions.append(txn)
        self.balance = txn.balance_after


# ---------------------------------------------------------------------------
# Storage layer
# ---------------------------------------------------------------------------


DEFAULT_DATA_FILE = Path.home() / ".shae-bank-data.json"


class BankStorage:
    """FILE SECTION — Data persistence"""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path if path is not None else DEFAULT_DATA_FILE

    def load(self) -> Dict[str, Account]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            accounts = {}
            for acc_data in raw.get("accounts", []):
                acc = Account.from_dict(acc_data)
                accounts[acc.id] = acc
            return accounts
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(c(f"WARNING: Could not load data file: {e}", "err"))
            return {}

    def save(self, accounts: Dict[str, Account]) -> None:
        data = {
            "accounts": [acc.to_dict() for acc in accounts.values()],
            "version": 1,
            "saved_at": datetime.now().isoformat(),
        }
        # Atomic write via temp file
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp.replace(self.path)


# ---------------------------------------------------------------------------
# Business logic
# ---------------------------------------------------------------------------


class Bank:
    """PROCEDURE DIVISION — Bank Operations"""

    def __init__(self, storage: BankStorage) -> None:
        self.storage = storage
        self.accounts = storage.load()

    def create_account(self, name: str) -> Account:
        acc_id = str(uuid.uuid4())
        open_date = datetime.now().isoformat()
        acc = Account(
            id=acc_id,
            name=name,
            open_date=open_date,
            balance=Decimal("0.00"),
            status="ACTIVE",
        )
        self.accounts[acc_id] = acc
        self.storage.save(self.accounts)
        return acc

    def get_account(self, query: str) -> Optional[Account]:
        # Match by ID (full or prefix) or name
        for acc in self.accounts.values():
            if acc.id == query or acc.id.startswith(query) or acc.name.lower() == query.lower():
                return acc
        return None

    def deposit(self, query: str, amount: Decimal, description: str = "") -> Optional[Account]:
        acc = self.get_account(query)
        if acc is None or acc.status != "ACTIVE":
            return None
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        new_balance = acc.balance + amount
        txn = Transaction(
            id=str(uuid.uuid4()),
            type=TransactionType.DEPOSIT,
            amount=amount,
            balance_after=new_balance,
            description=description or "Deposit",
        )
        acc.add_transaction(txn)
        self.storage.save(self.accounts)
        return acc

    def withdraw(self, query: str, amount: Decimal, description: str = "") -> Optional[Account]:
        acc = self.get_account(query)
        if acc is None or acc.status != "ACTIVE":
            return None
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > acc.balance:
            raise ValueError("Insufficient funds")
        new_balance = acc.balance - amount
        txn = Transaction(
            id=str(uuid.uuid4()),
            type=TransactionType.WITHDRAWAL,
            amount=amount,
            balance_after=new_balance,
            description=description or "Withdrawal",
        )
        acc.add_transaction(txn)
        self.storage.save(self.accounts)
        return acc

    def show_balance(self, query: str) -> Optional[Account]:
        return self.get_account(query)

    def show_history(self, query: str, limit: int = 20) -> Optional[List[Transaction]]:
        acc = self.get_account(query)
        if acc is None:
            return None
        return acc.transactions[-limit:]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_amount(s: str) -> Decimal:
    try:
        return Decimal(s).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception:
        raise ValueError(f"Invalid amount: {s}")


def format_amount(amount: Decimal) -> str:
    return f"{amount:,.2f}"


def print_account_summary(acc: Account) -> None:
    body = (
        f"Account ID : {acc.id}\n"
        f"Name       : {acc.name}\n"
        f"Opened     : {acc.open_date[:10]}\n"
        f"Status     : {acc.status}\n"
        f"Balance    : {c(format_amount(acc.balance), 'bold', 'ok')}"
    )
    print(panel("ACCOUNT SUMMARY", body))


def print_transactions(txns: List[Transaction]) -> None:
    if not txns:
        print(c("  No transactions.", "muted"))
        return
    header = f"  {'DATE':<19}  {'TYPE':<12}  {'AMOUNT':>12}  {'BALANCE':>12}  DESCRIPTION"
    print(c(header, "bold", "ink"))
    print(c("  " + "-" * 80, "muted"))
    for txn in reversed(txns):
        dt = txn.timestamp[:19].replace("T", " ")
        type_color = "ok" if txn.type == TransactionType.DEPOSIT else "err"
        amount_str = format_amount(txn.amount)
        balance_str = format_amount(txn.balance_after)
        print(
            f"  {dt:<19}  {c(txn.type.value, type_color):<12}  "
            f"{c(amount_str, type_color):>12}  {balance_str:>12}  {txn.description}"
        )


def main() -> None:
    bank = Bank(BankStorage())

    print(c("=" * 72, "muted"))
    print(c("  S H A E   \u00b7   C O B O L   B A N K   A C C O U N T   M A N A G E R", "bold", "ink"))
    print(c("  DATA DIVISION. PROCEDURE DIVISION. STOP RUN.", "muted"))
    print(c("=" * 72, "muted"))
    print()
    print(c("Commands: create, deposit, withdraw, balance, history, list, help, quit", "muted"))
    print()

    while True:
        try:
            raw = input(c(" BANK > ", "oxide", "bold")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print(c("Exiting...", "muted"))
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()
        args = parts[1:]

        try:
            if cmd in ("create", "new", "open"):
                if not args:
                    print(c("Usage: create <name>", "err"))
                    continue
                name = " ".join(args)
                acc = bank.create_account(name)
                print(c(f"\nAccount created: {acc.name} ({acc.id[:8]}...)", "ok"))
                print_account_summary(acc)

            elif cmd in ("deposit", "dep", "credit"):
                if len(args) < 2:
                    print(c("Usage: deposit <account> <amount> [description]", "err"))
                    continue
                query, amt_str = args[0], args[1]
                desc = " ".join(args[2:]) if len(args) > 2 else ""
                amount = parse_amount(amt_str)
                acc = bank.deposit(query, amount, desc)
                if acc is None:
                    print(c("Account not found or inactive.", "err"))
                else:
                    print(c(f"\nDeposit of {c(format_amount(amount), 'ok')} accepted.", "ok"))
                    print_account_summary(acc)

            elif cmd in ("withdraw", "wd", "debit"):
                if len(args) < 2:
                    print(c("Usage: withdraw <account> <amount> [description]", "err"))
                    continue
                query, amt_str = args[0], args[1]
                desc = " ".join(args[2:]) if len(args) > 2 else ""
                amount = parse_amount(amt_str)
                acc = bank.withdraw(query, amount, desc)
                if acc is None:
                    print(c("Account not found or inactive.", "err"))
                else:
                    print(c(f"\nWithdrawal of {c(format_amount(amount), 'err')} processed.", "ok"))
                    print_account_summary(acc)

            elif cmd in ("balance", "bal", "show"):
                if not args:
                    print(c("Usage: balance <account>", "err"))
                    continue
                query = args[0]
                acc = bank.show_balance(query)
                if acc is None:
                    print(c("Account not found.", "err"))
                else:
                    print_account_summary(acc)

            elif cmd in ("history", "hist", "transactions", "txns"):
                if not args:
                    print(c("Usage: history <account> [limit]", "err"))
                    continue
                query = args[0]
                limit = int(args[1]) if len(args) > 1 else 20
                txns = bank.show_history(query, limit)
                if txns is None:
                    print(c("Account not found.", "err"))
                else:
                    print(c(f"\nTransaction History (last {limit}):", "bold", "ink"))
                    print_transactions(txns)

            elif cmd in ("list", "ls", "accounts"):
                if not bank.accounts:
                    print(c("No accounts exist.", "muted"))
                else:
                    print(c("Existing Accounts:", "bold", "ink"))
                    for acc in bank.accounts.values():
                        print(f"  {acc.id[:8]}...  {acc.name:<20}  {format_amount(acc.balance):>12}  {acc.status}")

            elif cmd in ("help", "?"):
                help_text = (
                    "create <name>                - Open a new account\n"
                    "deposit <acc> <amt> [desc]   - Add funds\n"
                    "withdraw <acc> <amt> [desc]  - Remove funds\n"
                    "balance <acc>                - Show current balance\n"
                    "history <acc> [limit]        - Show transaction history\n"
                    "list                         - List all accounts\n"
                    "help / ?                     - Show this help\n"
                    "quit / exit                  - Exit the program"
                )
                print(panel("COMMANDS", help_text))

            elif cmd in ("quit", "exit"):
                print(c("Goodbye.", "muted"))
                break

            else:
                print(c(f"Unknown command: {cmd}. Type 'help'.", "err"))

        except ValueError as e:
            print(c(f"Error: {e}", "err"))
        except Exception as e:
            print(c(f"Unexpected error: {e}", "err"))

        print()


if __name__ == "__main__":
    main()