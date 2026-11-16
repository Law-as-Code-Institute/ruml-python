# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass

from ruml_parser.internal.ruml.nodes.abstract_node import AbstractNode


@dataclass(frozen=True, slots=True, kw_only=True)
class LeafNode(AbstractNode):
    pass
