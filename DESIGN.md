# SHAE COBOL Bank Account Manager — DESIGN.md

This document describes how the SHAE Field Manual design system is applied to
a CLI bank account manager that borrows its structure from COBOL.

## Design System Mapping

### 1. Precise over decorative

- Output uses monospaced ASCII frames (`┌─┐│└┘`, `═`) instead of emoji.
- Balances, dates, and transaction amounts are tabular and right-aligned.
- No ornamental noise: every line of output carries information.
- The prompt is compact: ` BANK > `.

### 2. Confident restraint

- Palette: near-black ink (`#191712`) on warm paper (`#F2EEE5`).
- Oxide red (`#B3341B` → SGR 124) is reserved for signals: prompts, errors,
  the `>>` / action markers, and withdrawal amounts.
- Deposit text is shown in ok green (`#2d6a2d`).
- No gradients, glows, shadows, or rounded panels — only hairline rules and
  border-defined boxes.

### 3. Density with air

- Account summaries are rendered inside border-defined panels.
- Blank lines separate sections so the eye can rest.
- Transaction history uses a compact aligned grid: date, type, amount,
  balance, description.

### 4. Motion is typesetting, state, and orientation

- A terminal cannot animate, so "motion" is expressed through state changes:
  balance updates, transaction appends, and account summary panels.
- State is always visible: `balance` prints a panel with account ID, name,
  status, and balance.

### 5. Accessibility is part of the aesthetic

- The game degrades gracefully when colour is unavailable (`TERM=dumb`,
  piped output, CI logs): all ANSI codes are stripped automatically.
- Keyboard-first: every action is a short text command.
- No time pressure: the program waits for input.
- Clear error messages: unknown commands are acknowledged, not ignored.
- Decimal arithmetic ensures exact financial values.

## Typography

- Terminal monospace font (user-configured).
- Uppercase only for COBOL-style field comments and short labels.
- Tabular alignment for numeric data (amounts right-aligned).

## Colour

| Token   | Terminal SGR | Hex approx | Use |
|---------|--------------|------------|-----|
| ink     | 38;5;16      | #191712    | Body text |
| paper   | 48;5;230     | #F2EEE5    | Background (when supported) |
| oxide   | 38;5;124     | #B3341B    | Prompts, withdrawals, errors, signals |
| muted   | 38;5;245     | #8a8a8a    | Metadata, hints |
| ok      | 38;5;22      | #2d6a2d    | Deposits, success messages |

## COBOL Heritage

- **DATA DIVISION**: `Account` and `Transaction` dataclasses modelled after
  fixed-format records with PIC-style comments.
- **PROCEDURE DIVISION**: `Bank` class with operations (create, deposit,
  withdraw, balance, history).
- **FILE SECTION**: `BankStorage` for sequential JSON persistence.
- **STOP RUN**: clean exit on `quit`.

## Persistence Details

- Data file: `~/.shae-bank-data.json` (default).
- Atomic writes via temp file + `os.replace()`.
- Decimal monetary amounts serialized as strings to preserve precision.

## Anti-patterns avoided

- No emoji, no ASCII art spam, no decorative borders.
- No colour for its own sake; colour is a signal, not decoration.
- No floating-point money; `Decimal` used throughout.
- No centred "hero" screen; the program opens directly into the prompt.

## Future extensions

- Interest accrual and monthly fees.
- Account deactivation / reactivation.
- Export statements to CSV.
- Multi-currency support.