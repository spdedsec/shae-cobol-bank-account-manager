#!/usr/bin/env python3
"""
SHAE COBOL Bank Account Manager
Production-grade CLI bank account manager with JSON persistence.
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List, Optional

DATA_FILE = Path.home() / '.local' / 'share' / 'shae-bank' / 'accounts.json'

@dataclass
class Transaction:
    type: str  # deposit, withdraw
    amount: str
    balance_after: str
    timestamp: str
    description: str = ""

@dataclass
class Account:
    id: str
    name: str
    balance: str
    created_at: str
    transactions: List[Transaction] = None
    
    def __post_init__(self):
        if self.transactions is None:
            self.transactions = []

def ensure_data_dir():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_accounts() -> dict:
    ensure_data_dir()
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
            # Convert dicts back to objects
            accounts = {}
            for k, v in data.items():
                transactions = [Transaction(**t) for t in v.get('transactions', [])]
                accounts[k] = Account(
                    id=v['id'], name=v['name'], balance=v['balance'],
                    created_at=v['created_at'], transactions=transactions
                )
            return accounts
    except Exception:
        return {}

def save_accounts(accounts: dict):
    ensure_data_dir()
    data = {}
    for k, v in accounts.items():
        data[k] = asdict(v)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def fmt_amount(amount: str) -> str:
    d = Decimal(amount)
    return f"{d:,.2f}"

def create_account(accounts: dict, name: str, initial: str = "0") -> Account:
    if any(a.name.lower() == name.lower() for a in accounts.values()):
        raise ValueError(f"Account with name '{name}' already exists")
    
    initial_decimal = Decimal(initial)
    if initial_decimal < 0:
        raise ValueError("Initial balance cannot be negative")
    
    account = Account(
        id=f"ACC{len(accounts)+1:04d}",
        name=name,
        balance=str(initial_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
        created_at=datetime.now().isoformat(),
        transactions=[]
    )
    if initial_decimal > 0:
        account.transactions.append(Transaction(
            type="deposit", amount=account.balance,
            balance_after=account.balance,
            timestamp=datetime.now().isoformat(),
            description="Initial deposit"
        ))
    accounts[account.id] = account
    return account

def find_account(accounts: dict, identifier: str) -> Optional[Account]:
    # Try by ID first
    if identifier in accounts:
        return accounts[identifier]
    # Try by name (case-insensitive)
    for acc in accounts.values():
        if acc.name.lower() == identifier.lower():
            return acc
    return None

def deposit(accounts: dict, identifier: str, amount: str) -> Account:
    acc = find_account(accounts, identifier)
    if not acc:
        raise ValueError(f"Account not found: {identifier}")
    
    amount_decimal = Decimal(amount)
    if amount_decimal <= 0:
        raise ValueError("Deposit amount must be positive")
    
    new_balance = (Decimal(acc.balance) + amount_decimal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    acc.balance = str(new_balance)
    acc.transactions.append(Transaction(
        type="deposit", amount=str(amount_decimal),
        balance_after=str(new_balance),
        timestamp=datetime.now().isoformat(),
        description="Deposit"
    ))
    return acc

def withdraw(accounts: dict, identifier: str, amount: str) -> Account:
    acc = find_account(accounts, identifier)
    if not acc:
        raise ValueError(f"Account not found: {identifier}")
    
    amount_decimal = Decimal(amount)
    if amount_decimal <= 0:
        raise ValueError("Withdrawal amount must be positive")
    
    current = Decimal(acc.balance)
    if amount_decimal > current:
        raise ValueError(f"Insufficient funds. Balance: {fmt_amount(acc.balance)}")
    
    new_balance = (current - amount_decimal).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    acc.balance = str(new_balance)
    acc.transactions.append(Transaction(
        type="withdraw", amount=str(amount_decimal),
        balance_after=str(new_balance),
        timestamp=datetime.now().isoformat(),
        description="Withdrawal"
    ))
    return acc

def print_account(acc: Account):
    print(f"\n{'=' * 50}")
    print(f" ACCOUNT: {acc.name} ({acc.id})")
    print(f"{'=' * 50}")
    print(f" Balance: ${fmt_amount(acc.balance)}")
    print(f" Created: {acc.created_at[:10]}")
    if acc.transactions:
        print(f"\n TRANSACTIONS ({len(acc.transactions)}):")
        print(f" {'DATE':<19} {'TYPE':<10} {'AMOUNT':>12} {'BALANCE':>12}  DESC")
        print(f" {'-'*60}")
        for t in acc.transactions[-10:]:  # Show last 10
            date = t.timestamp[:19].replace('T', ' ')
            sign = '+' if t.type == 'deposit' else '-'
            print(f" {date} {t.type:<10} {sign}{fmt_amount(t.amount):>11} ${fmt_amount(t.balance_after):>11}  {t.description}")
    else:
        print(" No transactions yet.")

def list_accounts(accounts: dict):
    if not accounts:
        print("No accounts found.")
        return
    print(f"\n{'ID':<8} {'NAME':<20} {'BALANCE':>12} {'TXNS':>4}")
    print(f"{'-'*50}")
    for acc in accounts.values():
        print(f" {acc.id:<7} {acc.name:<19} ${fmt_amount(acc.balance):>11} {len(acc.transactions):>4}")

def main():
    parser = argparse.ArgumentParser(
        prog='shae-bank',
        description='SHAE COBOL Bank Account Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  create <name> [initial]    Create new account
  deposit <id|name> <amount> Deposit funds
  withdraw <id|name> <amount> Withdraw funds
  balance <id|name>          Show account balance & history
  list                       List all accounts
  help                       Show this help
        """
    )
    parser.add_argument('command', nargs='?', choices=['create', 'deposit', 'withdraw', 'balance', 'list', 'help'], default='help')
    parser.add_argument('args', nargs='*')
    args = parser.parse_args()
    
    if args.command == 'help' or not args.command:
        parser.print_help()
        return
    
    accounts = load_accounts()
    
    try:
        if args.command == 'create':
            if not args.args:
                print("Usage: shae-bank create <name> [initial_balance]")
                return
            name = args.args[0]
            initial = args.args[1] if len(args.args) > 1 else "0"
            acc = create_account(accounts, name, initial)
            save_accounts(accounts)
            print(f"Account created: {acc.id} - {acc.name} (${fmt_amount(acc.balance)})")
        
        elif args.command == 'deposit':
            if len(args.args) < 2:
                print("Usage: shae-bank deposit <id|name> <amount>")
                return
            acc = deposit(accounts, args.args[0], args.args[1])
            save_accounts(accounts)
            print(f"Deposited ${fmt_amount(args.args[1])}. New balance: ${fmt_amount(acc.balance)}")
        
        elif args.command == 'withdraw':
            if len(args.args) < 2:
                print("Usage: shae-bank withdraw <id|name> <amount>")
                return
            acc = withdraw(accounts, args.args[0], args.args[1])
            save_accounts(accounts)
            print(f"Withdrew ${fmt_amount(args.args[1])}. New balance: ${fmt_amount(acc.balance)}")
        
        elif args.command == 'balance':
            if not args.args:
                print("Usage: shae-bank balance <id|name>")
                return
            acc = find_account(accounts, args.args[0])
            if not acc:
                print(f"Account not found: {args.args[0]}")
                return
            print_account(acc)
        
        elif args.command == 'list':
            list_accounts(accounts)
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
