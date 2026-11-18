#!/usr/bin/env python3
"""Ad-hoc smoke check (no third-party deps). Run: python3 smoke_check.py"""
import sys, os, tempfile
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import main

tmpdir = tempfile.mkdtemp()
path = Path(tmpdir) / "bank.json"
storage = main.BankStorage(path)
bank = main.Bank(storage)

acc = bank.create_account("Alice")
assert acc.name == "Alice"
assert acc.balance == Decimal("0.00")

bank.deposit(acc.id, Decimal("100.00"))
assert acc.balance == Decimal("100.00")
assert len(acc.transactions) == 1

bank.withdraw(acc.id, Decimal("25.00"))
assert acc.balance == Decimal("75.00")
assert len(acc.transactions) == 2

# Insufficient funds
try:
    bank.withdraw(acc.id, Decimal("1000.00"))
    assert False, "should raise"
except ValueError:
    pass

# Reload from disk
bank2 = main.Bank(main.BankStorage(path))
loaded = bank2.get_account(acc.id)
assert loaded is not None
assert loaded.balance == Decimal("75.00")

# Prefix lookup
assert bank2.get_account(acc.id[:8]) is loaded

# History
txns = bank2.show_history(acc.id, limit=10)
assert len(txns) == 2

assert main.parse_amount("10.5") == Decimal("10.50")
assert main.format_amount(Decimal("1234.5")) == "1,234.50"

assert main.c("hi") == "hi"
assert "HI" in main.c("HI", "bold", "oxide")

print("SMOKE CHECK PASSED")
