# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from ruml_parser.internal.ruml.aliases import ContextCategory, ContextType, Hash
from ruml_parser.model import ruml as model


@dataclass(frozen=True, slots=True, kw_only=True)
class Context:
    title: str
    """Title of the context entry"""
    category: ContextCategory
    """Category of the context"""
    type: ContextType = model.Type4.embedded
    """How the context content is carried"""
    timestamp: datetime
    """Modification time of the context"""
    subject: bool = False
    """Whether this context is the subject of the evaluation"""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    """Free-form metadata about the context"""
    content: Mapping[str, Any] | None = None
    """Embedded context content"""
    source: Mapping[str, Any] | None = None
    """Free-form description of the context source"""
    url: str | None = None
    """URL of the context; required for type 'url'"""
    container_path: str | None = None
    """Path to the context inside the RUML container (below `.context/`); required
    for type 'container'"""
    ref: str | None = None
    """Symbolic reference; required for type 'external'"""
    hash: Hash | None = None
    """Integrity hash"""
    access_date: date | None = None
    """Date the context url was last accessed"""
