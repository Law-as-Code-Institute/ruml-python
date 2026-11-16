# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass, field

from ruml_parser.internal.ruml.aliases import (
    CapabilityRole,
    OfficialCapabilityId,
    TextId,
)
from ruml_parser.internal.ruml.capability.abstract_capability_declaration import (
    AbstractCapabilityDeclaration,
)
from ruml_parser.internal.ruml.text_reference.text import Text


@dataclass(frozen=True, slots=True, kw_only=True)
class TextReferenceCapabilityDeclaration(AbstractCapabilityDeclaration):
    id = str(OfficialCapabilityId.ruml_text_reference)
    role = CapabilityRole.data

    required: bool = False
    """Whether this capability must be resolved to evaluate"""
    data: Mapping[TextId, Text] = field(default_factory=dict)
    """Text definitions, keyed by text id"""
