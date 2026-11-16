# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""The error for Structural violations found on the internal model (ADR 0001)."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StructuralViolation:
    """One violated spec rule, with every location that violates it."""

    rule: str
    """The RUML spec's code for the rule, e.g. ``OP-02``."""
    message: str
    paths: Sequence[str]
    """JSON Pointers of the offending locations in the RUML document."""


class RumlStructuralError(ValueError):
    """Raised by ``to_internal``'s validators when a document violates a rule the schema cannot express.

    Like ``RumlValidationError`` for the schema, it collects every violation found, so a
    caller learns about all of them at once.
    """

    violations: list[StructuralViolation]

    def __init__(self, violations: Iterable[StructuralViolation]):
        self.violations = list(violations)
        super().__init__(
            "; ".join(
                f"{violation.message} (spec rule {violation.rule})"
                for violation in self.violations
            )
        )
