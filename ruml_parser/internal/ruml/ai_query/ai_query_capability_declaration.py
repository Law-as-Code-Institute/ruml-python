# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from ruml_parser.internal.ruml.aliases import CapabilityRole, OfficialCapabilityId
from ruml_parser.internal.ruml.capability.abstract_capability_declaration import (
    AbstractCapabilityDeclaration,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class AiQueryDeclarationConfig:
    system_prompt: str | None = None
    """System prompt applied to all AI queries in the document"""


@dataclass(frozen=True, slots=True, kw_only=True)
class AiQueryCapabilityDeclaration(AbstractCapabilityDeclaration):
    id = str(OfficialCapabilityId.ruml_ai_query)
    role = CapabilityRole.decision

    required: bool = False
    """Whether this capability must be resolved to evaluate"""
    config: AiQueryDeclarationConfig | None = None
    """Root-level configuration for the AI query capability"""
