# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import dataclass

from ruml_parser.internal.ruml.aliases import (
    OfficialCapabilityId,
    TextAnchorType,
    TextId,
)
from ruml_parser.internal.ruml.capability.abstract_node_capability import (
    AbstractNodeCapability,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class TextAnchor:
    id: TextId
    """Key of the text entry in this RUML's own data"""
    type: TextAnchorType
    """`represents`: the norm the node implements; `refers-to`: a text it refers to"""
    element: str | None = None
    """GUID of an element of the entry's RUML Text; none for the whole text"""


@dataclass(frozen=True, slots=True, kw_only=True)
class TextRefsNodeCapability(AbstractNodeCapability):
    """The texts a node is linked to (§4.12); at most one anchor `represents`."""

    id = str(OfficialCapabilityId.ruml_text_reference)

    refs: Sequence[TextAnchor]
