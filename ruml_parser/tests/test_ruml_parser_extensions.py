# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""``RumlParser`` validating the payloads of a capability extension's capability."""

from typing import Any

import pytest

from ruml_parser.ruml_parser import RumlParser
from ruml_parser.schema_validation import RumlValidationError
from ruml_parser.tests.greeting_extension import GREETING_ID, GreetingExtension
from ruml_parser.tests.ruml_builders import (
    node,
    ruml_document,
    unchecked_capability,
    unchecked_node_capability,
)
from ruml_parser.tests.ruml_dict import RumlRulemappingLogicFormatDict


def greeting_document(
    root_payload: dict[str, Any], node_payload: dict[str, Any]
) -> RumlRulemappingLogicFormatDict:
    """A document declaring ``com.example/greeting`` and using it on its single node."""
    return ruml_document(
        capabilities=[unchecked_capability(GREETING_ID, root_payload, role="data")],
        rulemap={
            "nodes": {
                "1": node(
                    capabilities=[unchecked_node_capability(GREETING_ID, node_payload)]
                )
            }
        },
    )


def test_accepts_payloads_of_the_extension_s_shape() -> None:
    # Arrange
    document = greeting_document({"salutation": "Hello"}, {"name": "world"})

    # Act
    result = RumlParser(extensions=[GreetingExtension()]).parse_dict(document)

    # Assert
    assert list(result.capabilities.declaration_order) == [GREETING_ID]


@pytest.mark.parametrize(
    ("document", "path"),
    [
        pytest.param(
            greeting_document({"salute": "Hello"}, {"name": "world"}),
            "/capabilities/0/payload",
            id="root",
        ),
        pytest.param(
            greeting_document({"salutation": "Hello"}, {"name": 42}),
            "/rulemap/nodes/1/capabilities/0/payload/name",
            id="node",
        ),
    ],
)
def test_rejects_payloads_of_another_shape(
    document: RumlRulemappingLogicFormatDict, path: str
) -> None:
    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        RumlParser(extensions=[GreetingExtension()]).parse_dict(document)
    assert path in excinfo.value.paths


def test_accepts_any_payload_without_the_extension() -> None:
    # Arrange
    document = greeting_document({"salute": "Hello"}, {"name": 42})

    # Act
    result = RumlParser().parse_dict(document)

    # Assert
    assert result.capabilities is not None


def test_still_rejects_what_the_ruml_schema_rejects() -> None:
    # Arrange
    valid = greeting_document({"salutation": "Hello"}, {"name": "world"})
    invalid = {**valid, "$specVersion": "not a version"}

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        RumlParser(extensions=[GreetingExtension()]).parse_dict(invalid)
    assert excinfo.value.paths == ["/$specVersion"]
