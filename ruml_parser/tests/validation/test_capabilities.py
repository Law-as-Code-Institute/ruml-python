# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest
from ruml_parser.internal.ruml import (
    BranchNode,
    CapabilityDeclarations,
    CapabilityDeclarationWithData,
    CapabilityRole,
    ExpressionCapabilityDeclaration,
    ExpressionNodeCapability,
    ExtensionCapabilityDeclaration,
    ExtensionNodeCapability,
    LeafNode,
    Metadata,
    NodeCapabilities,
    NodeCapability,
    Operator,
    OtherNodeCapability,
    RumlDocument,
)
from ruml_parser.internal.validation.capabilities import (
    reject_invalid_number_of_combiners_per_node,
)
from ruml_parser.model.ruml import DocumentStatus
from ruml_parser.structural_error import RumlStructuralError

NODE_ID = UUID("71946db2-13e2-49df-9f7b-59369cff7679")
TIMESTAMP = datetime(2026, 8, 20, 12, tzinfo=UTC)
metadata = Metadata(
    id=NODE_ID,
    version="1.0.0",
    created=TIMESTAMP,
    modified=TIMESTAMP,
    status=DocumentStatus.draft,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CombinerACapabilityDeclaration(ExtensionCapabilityDeclaration):
    id = "com.example/combiner-a"
    role = CapabilityRole.combiner


@dataclass(frozen=True, slots=True, kw_only=True)
class CombinerANodeCapability(ExtensionNodeCapability):
    id = "com.example/combiner-a"


@dataclass(frozen=True, slots=True, kw_only=True)
class CombinerBCapabilityDeclaration(ExtensionCapabilityDeclaration):
    id = "com.example/combiner-b"
    role = CapabilityRole.combiner


@dataclass(frozen=True, slots=True, kw_only=True)
class CombinerBNodeCapability(ExtensionNodeCapability):
    id = "com.example/combiner-b"


def delegated_document(
    capabilities: CapabilityDeclarations, entries: Sequence[NodeCapability]
) -> RumlDocument:
    return RumlDocument(
        spec_version="1.0",
        metadata=metadata,
        capabilities=capabilities,
        nodes={
            "1": BranchNode(
                id=NODE_ID,
                label="root",
                operator=Operator.DELEGATED,
                capabilities=NodeCapabilities(entries=entries),
            )
        },
    )


class TestRejectInvalidNumberOfCombinersPerNode:
    def test_succeeds_on_delegated_node_with_one_ruml_expression(self):
        # Arrange
        document = RumlDocument(
            spec_version="1.0",
            metadata=metadata,
            capabilities=CapabilityDeclarations(
                expression=ExpressionCapabilityDeclaration()
            ),
            nodes={
                "1": BranchNode(
                    id=NODE_ID,
                    label="root",
                    operator=Operator.DELEGATED,
                    capabilities=NodeCapabilities(
                        entries=[
                            ExpressionNodeCapability(
                                expression="$children[0]",
                                description="Follows the first child",
                            )
                        ]
                    ),
                )
            },
        )

        # Act / Assert: does not raise
        reject_invalid_number_of_combiners_per_node(document)

    def test_fails_on_delegated_node_with_no_ruml_expression(self):
        # Arrange
        document = RumlDocument(
            spec_version="1.0",
            metadata=metadata,
            nodes={
                "1": BranchNode(
                    id=NODE_ID,
                    label="root",
                    operator=Operator.DELEGATED,
                )
            },
        )

        # Act / Assert
        with pytest.raises(
            RumlStructuralError, match="node '1' has 0 combiners"
        ) as excinfo:
            reject_invalid_number_of_combiners_per_node(document)
        assert [violation.paths for violation in excinfo.value.violations] == [
            ["/rulemap/nodes/1"]
        ]
        assert [violation.rule for violation in excinfo.value.violations] == ["OP-02"]

    def test_points_at_the_declaration_of_a_capability_that_is_no_combiner(self):
        # Arrange
        document = delegated_document(
            CapabilityDeclarations(
                extensions={
                    CombinerACapabilityDeclaration.id: CombinerACapabilityDeclaration()
                },
                third_party={
                    "com.example/data": CapabilityDeclarationWithData(
                        id="com.example/data", role=CapabilityRole.data
                    )
                },
                declaration_order=[
                    CombinerACapabilityDeclaration.id,
                    "com.example/data",
                ],
            ),
            [OtherNodeCapability(id="com.example/data")],
        )

        # Act / Assert
        with pytest.raises(
            RumlStructuralError, match="node '1' has 0 combiner"
        ) as excinfo:
            reject_invalid_number_of_combiners_per_node(document)
        assert [violation.paths for violation in excinfo.value.violations] == [
            ["/capabilities/1", "/rulemap/nodes/1"]
        ]

    def test_fails_on_delegated_node_with_multiple_combiners(self):
        # Arrange
        document = RumlDocument(
            spec_version="1.0",
            metadata=metadata,
            capabilities=CapabilityDeclarations(
                expression=ExpressionCapabilityDeclaration(),
                third_party={
                    "com.example/combine": CapabilityDeclarationWithData(
                        id="com.example/combine", role=CapabilityRole.combiner
                    )
                },
            ),
            nodes={
                "1": BranchNode(
                    id=NODE_ID,
                    label="root",
                    operator=Operator.DELEGATED,
                    capabilities=NodeCapabilities(
                        entries=[
                            ExpressionNodeCapability(
                                expression="$children[0]",
                                description="Follows the first child",
                            ),
                            OtherNodeCapability(id="com.example/combine"),
                        ]
                    ),
                )
            },
        )

        # Act / Assert
        with pytest.raises(ValueError, match="node '1' has 2 combiners"):
            reject_invalid_number_of_combiners_per_node(document)

    def test_succeeds_on_delegated_node_with_one_custom_combiner(self):
        # Arrange
        document = delegated_document(
            CapabilityDeclarations(
                extensions={
                    CombinerACapabilityDeclaration.id: CombinerACapabilityDeclaration()
                }
            ),
            [CombinerANodeCapability()],
        )

        # Act / Assert: does not raise
        reject_invalid_number_of_combiners_per_node(document)

    def test_fails_on_delegated_node_with_multiple_custom_combiners(self):
        # Arrange
        document = delegated_document(
            CapabilityDeclarations(
                extensions={
                    CombinerACapabilityDeclaration.id: CombinerACapabilityDeclaration(),
                    CombinerBCapabilityDeclaration.id: CombinerBCapabilityDeclaration(),
                }
            ),
            [CombinerANodeCapability(), CombinerBNodeCapability()],
        )

        # Act / Assert
        with pytest.raises(
            RumlStructuralError, match="node '1' has 2 combiners"
        ) as excinfo:
            reject_invalid_number_of_combiners_per_node(document)
        [violation] = excinfo.value.violations
        assert violation.rule == "OP-02"
        assert violation.paths == ["/rulemap/nodes/1/capabilities/1"]

    def test_fails_on_delegated_node_with_ruml_expression_and_custom_combiner(self):
        # Arrange
        document = delegated_document(
            CapabilityDeclarations(
                expression=ExpressionCapabilityDeclaration(),
                extensions={
                    CombinerACapabilityDeclaration.id: CombinerACapabilityDeclaration()
                },
            ),
            [
                ExpressionNodeCapability(
                    expression="$children[0]", description="Follows the first child"
                ),
                CombinerANodeCapability(),
            ],
        )

        # Act / Assert
        with pytest.raises(ValueError, match="node '1' has 2 combiners"):
            reject_invalid_number_of_combiners_per_node(document)

    def test_fails_on_leaf_node_with_combiner(self):
        # Arrange
        document = RumlDocument(
            spec_version="1.0",
            metadata=metadata,
            capabilities=CapabilityDeclarations(
                extensions={
                    CombinerACapabilityDeclaration.id: CombinerACapabilityDeclaration()
                }
            ),
            nodes={
                "1": LeafNode(
                    id=NODE_ID,
                    label="root",
                    capabilities=NodeCapabilities(entries=[CombinerANodeCapability()]),
                )
            },
        )

        # Act / Assert
        with pytest.raises(
            RumlStructuralError, match="node '1' has 1 combiners"
        ) as excinfo:
            reject_invalid_number_of_combiners_per_node(document)
        assert [violation.paths for violation in excinfo.value.violations] == [
            ["/rulemap/nodes/1"]
        ]
        assert [violation.rule for violation in excinfo.value.violations] == ["CAP-08"]

    def test_fails_on_and_node_with_combiner(self):
        # Arrange
        document = RumlDocument(
            spec_version="1.0",
            metadata=metadata,
            capabilities=CapabilityDeclarations(
                extensions={
                    CombinerACapabilityDeclaration.id: CombinerACapabilityDeclaration()
                }
            ),
            nodes={
                "1": BranchNode(
                    id=NODE_ID,
                    label="root",
                    operator=Operator.AND,
                    capabilities=NodeCapabilities(entries=[CombinerANodeCapability()]),
                )
            },
        )

        # Act / Assert
        with pytest.raises(
            RumlStructuralError, match="node '1' has 1 combiners"
        ) as excinfo:
            reject_invalid_number_of_combiners_per_node(document)
        assert [violation.paths for violation in excinfo.value.violations] == [
            ["/rulemap/nodes/1"]
        ]
        assert [violation.rule for violation in excinfo.value.violations] == ["CAP-08"]
