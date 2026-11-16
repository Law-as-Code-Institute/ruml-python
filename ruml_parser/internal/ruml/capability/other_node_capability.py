# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from ruml_parser.internal.ruml.aliases import CapabilityId, CapabilityPayload
from ruml_parser.internal.ruml.capability.abstract_node_capability import (
    AbstractNodeCapability,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class OtherNodeCapability(AbstractNodeCapability):
    """A node-level capability entry the internal model has no dedicated type for.

    Draft ids and third-party ids that no extension models, and ``ruml:datapoints``
    (which has no node-level model), keep their free-form payload here.
    """

    id: CapabilityId
    payload: CapabilityPayload | None = None
    """The entry's payload; `None` for an entry that carries none"""
