# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ruml_parser.internal.ruml.aliases import OfficialCapabilityId
from ruml_parser.internal.ruml.capability.abstract_node_capability import (
    AbstractNodeCapability,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Action:
    operation: str
    """The operation to perform (open vocabulary)"""
    ref: str
    """Symbolic reference to the operation implementation"""
    config: Mapping[str, Any] | None = None
    """Optional, runtime-defined configuration for the action"""


@dataclass(frozen=True, slots=True, kw_only=True)
class ActionsNodeCapability(AbstractNodeCapability):
    """The actions declared for a node; at least one of the three is set.

    The schema expresses "at least one" as an `anyOf` over three otherwise identical
    objects, which the codegen renders as `Actions1 | Actions2 | Actions3`.
    """

    id = str(OfficialCapabilityId.ruml_actions)

    description: str | None = None
    """Description of the actions declared for the node"""
    on_true: Action | None = None
    """Action to run when the node evaluates to true"""
    on_false: Action | None = None
    """Action to run when the node evaluates to false"""
    on_undefined: Action | None = None
    """Action to run when the node evaluates to undefined"""
