# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
from typing import Any, override

import pytest

from ruml_parser.internal import ruml as internal
from ruml_parser.internal.mapping import to_internal
from ruml_parser.model.ruml import RumlRulemappingLogicFormat
from ruml_parser.structural_error import RumlStructuralError
from ruml_parser.tests.greeting_extension import (
    GREETING_ID,
    GreetingExtension,
    GreetingNodeCapability,
    GreetingsCapabilityDeclaration,
)
from ruml_parser.tests.ruml_builders import (
    node,
    ruml_document,
    unchecked_capability,
    unchecked_node_capability,
)
from ruml_parser.tests.ruml_dict import RumlRulemappingLogicFormatDict


def greeting_document(payload: dict[str, Any]) -> RumlRulemappingLogicFormatDict:
    """A document declaring ``com.example/greeting`` as required, with ``payload``."""
    return ruml_document(
        capabilities=[
            unchecked_capability(GREETING_ID, payload, required=True, role="data")
        ]
    )


def greeting_node_document(
    payload: dict[str, Any],
) -> RumlRulemappingLogicFormatDict:
    """A document whose single node uses ``com.example/greeting`` with ``payload``."""
    return ruml_document(
        capabilities=[
            unchecked_capability(GREETING_ID, {"salutation": "Hello"}, role="data")
        ],
        rulemap={
            "nodes": {
                "1": node(
                    capabilities=[unchecked_node_capability(GREETING_ID, payload)]
                )
            }
        },
    )


def map_with_extension(
    document: RumlRulemappingLogicFormatDict,
) -> internal.RumlDocument:
    parsed = RumlRulemappingLogicFormat.model_validate(document)
    return to_internal(parsed, [GreetingExtension()])


def test_extension_models_the_declaration_of_its_capability() -> None:
    # Arrange
    document = greeting_document({"salutation": "Hello"})

    # Act
    result = map_with_extension(document)

    # Assert
    assert result.capabilities == internal.CapabilityDeclarations(
        extensions={
            GREETING_ID: GreetingsCapabilityDeclaration(
                required=True, salutation="Hello"
            )
        }
    )


def test_declaration_is_found_by_its_type() -> None:
    # Arrange
    document = greeting_document({"salutation": "Hello"})

    # Act
    result = map_with_extension(document)

    # Assert
    assert result.capabilities.extension(
        GreetingsCapabilityDeclaration
    ) == GreetingsCapabilityDeclaration(required=True, salutation="Hello")


def test_declaration_of_an_undeclared_capability_is_none() -> None:
    # Arrange
    document = ruml_document()

    # Act
    result = map_with_extension(document)

    # Assert
    assert result.capabilities.extension(GreetingsCapabilityDeclaration) is None


def test_payload_must_have_the_shape_the_extension_prescribes() -> None:
    # Arrange
    document = greeting_document({"salute": "Hello"})

    # Act / Assert
    with pytest.raises(ValueError, match=f"'{GREETING_ID}' does not have the shape"):
        map_with_extension(document)


def test_a_declared_role_other_than_the_extension_s_is_rejected() -> None:
    # Arrange: `GreetingExtension` implements a `data` capability (CAP-04)
    document = ruml_document(
        capabilities=[
            unchecked_capability(GREETING_ID, {"salutation": "Hello"}, role="decision")
        ]
    )

    # Act / Assert
    with pytest.raises(RumlStructuralError) as excinfo:
        map_with_extension(document)
    [violation] = excinfo.value.violations
    assert violation.rule == "CAP-04"
    assert violation.paths == ["/capabilities/0/role"]


def test_extension_models_the_node_entries_of_its_capability() -> None:
    # Arrange
    document = greeting_node_document({"name": "world"})

    # Act
    result = map_with_extension(document)

    # Assert
    assert result.nodes["1"].capabilities == internal.NodeCapabilities(
        entries=[GreetingNodeCapability(name="world")]
    )


def test_node_payload_must_have_the_shape_the_extension_prescribes() -> None:
    # Arrange
    document = greeting_node_document({"nom": "world"})

    # Act / Assert
    with pytest.raises(ValueError, match=f"'{GREETING_ID}' does not have the shape"):
        map_with_extension(document)


class RecordingGreetingExtension(GreetingExtension):
    """``GreetingExtension``, recording the documents it is asked to validate."""

    def __init__(self) -> None:
        self.validated: list[internal.RumlDocument] = []

    @override
    def validate(self, document: internal.RumlDocument) -> None:
        self.validated.append(document)


def test_extension_validates_the_document_built_with_it() -> None:
    # Arrange
    extension = RecordingGreetingExtension()
    document = RumlRulemappingLogicFormat.model_validate(
        greeting_document({"salutation": "Hello"})
    )

    # Act
    result = to_internal(document, [extension])

    # Assert
    assert extension.validated == [result]
