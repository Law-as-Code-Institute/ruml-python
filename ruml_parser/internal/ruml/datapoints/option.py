# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class Option:
    value: str
    """Value of the option"""
    label: str | None = None
    """Human-readable label for the option"""
