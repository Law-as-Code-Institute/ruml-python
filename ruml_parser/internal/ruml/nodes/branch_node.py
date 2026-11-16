# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import dataclass, field

from ruml_parser.internal.ruml.aliases import LexId, Operator
from ruml_parser.internal.ruml.nodes.abstract_node import AbstractNode


@dataclass(frozen=True, slots=True, kw_only=True)
class BranchNode(AbstractNode):
    operator: Operator
    """Logical operator combining the outcomes of the child nodes"""
    children: Sequence[LexId] = field(default_factory=list)
    """Ordered lexIds of the child nodes"""
