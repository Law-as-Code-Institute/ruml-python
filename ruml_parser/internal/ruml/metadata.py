# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ruml_parser.internal.ruml.aliases import (
    DerivationType,
    DocumentStatus,
    DocumentType,
    Hash,
    LanguageCode,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Author:
    name: str
    """Name of the author"""
    email: str | None = None
    """Optional email of the author"""
    organization: str | None = None
    """Institutional affiliation of the author, not the document's publisher"""


@dataclass(frozen=True, slots=True, kw_only=True)
class DerivedFrom:
    original_id: UUID
    """The id of the original document"""
    original_hash: Hash | None = None
    """The hash of the original document"""
    original_status: DocumentStatus
    """The status of the original at the time of copying"""
    derivation_type: DerivationType
    """How this document was derived from the original"""
    derived_at: datetime
    """The timestamp of the copy creation"""
    derived_by: str | None = None
    """Creating entity/person"""


@dataclass(frozen=True, slots=True, kw_only=True)
class Metadata:
    id: UUID
    """Unique identifier of the RUML file"""
    title: str | None = None
    """Title of the rulemap"""
    description: str | None = None
    """Description of what the rulemap represents"""
    version: str
    """Content version"""
    created: datetime
    """Creation timestamp"""
    modified: datetime
    """Timestamp of the last modification"""
    status: DocumentStatus
    """The status of the RUML file"""
    comment: str | None = None
    """Free-text comment on the document, e.g. the reason for status `suspended`"""
    document_type: DocumentType | None = None
    """The type of the document"""
    authors: Sequence[Author] = field(default_factory=list)
    """List of authors"""
    organization: str | None = None
    """Publishing organization who is institutionally responsible for the document"""
    jurisdiction: str | None = None
    """Jurisdiction, e.g. `DE` or `DE-BY`"""
    legal_domain: str | None = None
    """Legal domain"""
    tags: Sequence[str] = field(default_factory=list)
    """Categorization/tagging"""
    derived_from: DerivedFrom | None = None
    """Derivation of the document"""
    language: LanguageCode | None = None
    valid_from: datetime | None = None
    """Validity start date"""
    valid_until: datetime | None = None
    """Validity end date"""
    replaces: UUID | None = None
    """Reference to a replaced version"""
    replaced_by: UUID | None = None
    """Reference to a successor version"""
