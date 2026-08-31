"""Shared test helpers (extracted from test modules — see audit 2026-08-31).

Importing helpers across test *modules* created implicit coupling; this
package is the neutral home. Dates are dynamic to avoid time-bomb
assertions (PR #34 lesson).
"""
