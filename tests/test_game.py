# ========================================================================
# SHAE COBOL Bank Account Manager — Test Suite
# ========================================================================

import sys
import os
import tempfile
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import main


def make_bank(tmpdir=None):
    path = Path(tmpdir or tempfile.mkdtemp()) / "bank.json"
    return main.Bank(main.BankStorage(path))


def test_create_account():
    bank = make_bank()
    acc = bank.create_account("Alice")
    assert acc.name == "Alice"
    assert acc.balance == Decimal("0.00")
    assert acc.status == "ACTIVE"
    assert acc.id in bank.accounts


def test_deposit():
    bank = make_bank()
    acc = bank.create_account("Bob")
    bank.deposit(acc.id, Decimal("100.00"))
    assert acc.balance == Decimal("100.00")
    assert len(acc.transactions) == 1
    assert acc.transactions[0].type == main.TransactionType.DEPOSIT


def test_withdraw():
    bank = make_bank()
    acc = bank.create_account("Carol")
    bank.deposit(acc.id, Decimal("50.00"))
    bank.withdraw(acc.id, Decimal("20.00"))
    assert acc.balance == Decimal("30.00")
    assert len(acc.transactions) == 2


def test_withdraw_insufficient():
    bank = make_bank()
    acc = bank.create_account("Dave")
    bank.deposit(acc.id, Decimal("10.00"))
    try:
        bank.withdraw(acc.id, Decimal("50.00"))
        assert False, "should raise"
    except ValueError as e:
        assert "Insufficient" in str(e)


def test_deposit_negative():
    bank = make_bank()
    acc = bank.create_account("Eve")
    try:
        bank.deposit(acc.id, Decimal("-10.00"))
        assert False, "should raise"
    except ValueError:
        pass


def test_withdraw_negative():
    bank = make_bank()
    acc = bank.create_account("Frank")
    bank.deposit(acc.id, Decimal("100.00"))
    try:
        bank.withdraw(acc.id, Decimal("-5.00"))
        assert False, "should raise"
    except ValueError:
        pass


def test_persistence():
    tmpdir = tempfile.mkdtemp()
    path = Path(tmpdir) / "bank.json"
    storage = main.BankStorage(path)
    bank = main.Bank(storage)
    acc = bank.create_account("Grace")
    bank.deposit(acc.id, Decimal("25.00"))

    # Reload from disk
    bank2 = main.Bank(main.BankStorage(path))
    loaded = bank2.get_account(acc.id)
    assert loaded is not None
    assert loaded.name == "Grace"
    assert loaded.balance == Decimal("25.00")
    assert len(loaded.transactions) == 1


def test_get_account_by_name():
    bank = make_bank()
    acc = bank.create_account("Heidi")
    assert bank.get_account("Heidi") is acc
    assert bank.get_account("heidi") is acc


def test_get_account_by_prefix():
    bank = make_bank()
    acc = bank.create_account("Ivan")
    prefix = acc.id[:8]
    assert bank.get_account(prefix) is acc


def test_history():
    bank = make_bank()
    acc = bank.create_account("Judy")
    for i in range(5):
        bank.deposit(acc.id, Decimal("10.00"))
    txns = bank.show_history(acc.id, limit=3)
    assert len(txns) == 3


def test_parse_amount():
    assert main.parse_amount("10.5") == Decimal("10.50")
    assert main.parse_amount("100") == Decimal("100.00")


def test_format_amount():
    assert main.format_amount(Decimal("1234.5")) == "1,234.50"


def test_balance_updates():
    bank = make_bank()
    acc = bank.create_account("Karl")
    bank.deposit(acc.id, Decimal("200.00"))
    bank.withdraw(acc.id, Decimal("50.00"))
    assert acc.balance == Decimal("150.00")
    assert acc.transactions[-1].balance_after == Decimal("150.00")


def test_zero_amount_rejected():
    bank = make_bank()
    acc = bank.create_account("Laura")
    try:
        bank.deposit(acc.id, Decimal("0.00"))
        assert False, "should raise"
    except ValueError:
        pass


def test_account_not_found():
    bank = make_bank()
    assert bank.get_account("nonexistent") is None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])