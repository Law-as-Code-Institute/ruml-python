# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ruml_parser.internal.ruml.aliases import (
    Hash,
    LanguageCode,
    LegislativeStatus,
    TextType,
)
from ruml_parser.model import ruml as model
from ruml_parser.text import text_of


@dataclass(frozen=True, slots=True, kw_only=True)
class TextSource:
    uri: str
    """URI of the source document a text's content was imported from"""
    digest: Hash | None = None
    """Digest of the archived source document"""
    terms: str | None = None
    """URI of the source's reuse terms"""


@dataclass(frozen=True, slots=True, kw_only=True)
class Text:
    title: str
    """Human-readable title of the text"""
    timestamp: datetime
    """When the author retrieved and recorded this text"""
    uri: str | None = None
    """URI of the text as published by its source; none for texts written in the
    RUML file itself"""
    status: LegislativeStatus | None = None
    """Legislative status of the text"""
    type: TextType = model.Type2.embedded
    """How the text content is carried"""
    text: str | None = None
    """Plain text; an embedded text carries this or `content`"""
    content: Mapping[str, Any] | None = None
    """Structured text in RUML Text form (§4.12), as JSON"""
    digest: Hash | None = None
    """SHA3-256 over the RFC 8785 form of `content`"""
    source: TextSource | None = None
    """The source document `content` was imported from"""
    url: str | None = None
    """URL of the text; required for type 'url'"""
    container_path: str | None = None
    """Path to the text inside the RUML container (below `.texts/`); required for
    type 'container'"""
    ref: str | None = None
    """Symbolic reference; required for type 'external'"""
    version: str | None = None
    """Version of the text"""
    valid_from: datetime | None = None
    """Validity start date"""
    valid_until: datetime | None = None
    """Validity end date"""
    language: LanguageCode | None = None
    is_referenced: bool = True
    """Whether the text is referenced by at least one node"""

    @property
    def plain_text(self) -> str | None:
        """The readable text of `content`, else `text`, else none."""
        return self.text if self.content is None else text_of(self.content)
