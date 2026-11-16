# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from ruml_parser.internal.ruml.aliases import CapabilityRole, OfficialCapabilityId
from ruml_parser.internal.ruml.capability.abstract_capability_declaration import (
    AbstractCapabilityDeclaration,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class TreeReferenceCapabilityDeclaration(AbstractCapabilityDeclaration):
    """Root-level declaration of `ruml:tree-reference`, which has no payload (TREE-01)."""

    id = str(OfficialCapabilityId.ruml_tree_reference)
    role = CapabilityRole.data

    required: bool = False
    """Whether this capability must be resolved to evaluate"""


@dataclass(frozen=True, slots=True, kw_only=True)
class TreeIncludeCapabilityDeclaration(AbstractCapabilityDeclaration):
    """Root-level declaration of `ruml:tree-include`, which has no payload (TREE-01)."""

    id = str(OfficialCapabilityId.ruml_tree_include)
    role = CapabilityRole.decision

    required: bool = False
    """Whether this capability must be resolved to evaluate"""
