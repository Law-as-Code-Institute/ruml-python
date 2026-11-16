# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""``RumlParser``: each form of RUML input checked and parsed alike."""

import json
from collections.abc import Callable
from typing import Any

import pytest

from ruml_parser.internal.ruml import RumlDocument
from ruml_parser.model.ruml import RumlRulemappingLogicFormat
from ruml_parser.ruml_parser import RumlParser
from ruml_parser.schema_validation import RumlValidationError
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

type Parse = Callable[[RumlParser, RumlRulemappingLogicFormatDict], RumlDocument]
"""Hands a document to a ``RumlParser`` in one of the forms it accepts."""


def _parse_json(
    parser: RumlParser, document: RumlRulemappingLogicFormatDict
) -> RumlDocument:
    return parser.parse_json(json.dumps(document))


def _parse_dict(
    parser: RumlParser, document: RumlRulemappingLogicFormatDict
) -> RumlDocument:
    return parser.parse_dict(document)


def _parse_model(
    parser: RumlParser, document: RumlRulemappingLogicFormatDict
) -> RumlDocument:
    return parser.parse_model(RumlRulemappingLogicFormat.model_validate(document))


PARSE_FROM_EACH_FORM = [
    pytest.param(_parse_json, id="json"),
    pytest.param(_parse_dict, id="dict"),
    pytest.param(_parse_model, id="model"),
]


def greeting_document(
    root_payload: dict[str, Any],
    node_payload: dict[str, Any],
    *,
    declared: bool = True,
) -> RumlRulemappingLogicFormatDict:
    """A document using ``com.example/greeting`` on its single node.

    Its root declares the capability unless ``declared`` is false: then it declares
    another one, which the schema accepts, but the spec forbids (no implicit
    capabilities).
    """
    declared_id = GREETING_ID if declared else "com.example/other"
    return ruml_document(
        capabilities=[unchecked_capability(declared_id, root_payload, role="data")],
        rulemap={
            "nodes": {
                "1": node(
                    capabilities=[unchecked_node_capability(GREETING_ID, node_payload)]
                )
            }
        },
    )


@pytest.mark.parametrize("parse", PARSE_FROM_EACH_FORM)
def test_models_the_extension_s_capability(parse: Parse) -> None:
    # Arrange
    parser = RumlParser(extensions=[GreetingExtension()])
    document = greeting_document({"salutation": "Hello"}, {"name": "world"})

    # Act
    result = parse(parser, document)

    # Assert
    assert result.capabilities.extension(
        GreetingsCapabilityDeclaration
    ) == GreetingsCapabilityDeclaration(salutation="Hello")
    assert list(result.all_node_capabilities_of_type(GreetingNodeCapability)) == [
        ("1", GreetingNodeCapability(name="world"))
    ]


@pytest.mark.parametrize("parse", PARSE_FROM_EACH_FORM)
def test_rejects_a_payload_against_the_extension_s_schema(parse: Parse) -> None:
    # Arrange
    parser = RumlParser(extensions=[GreetingExtension()])
    document = greeting_document({"salutation": "Hello"}, {"name": 42})

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        parse(parser, document)
    assert excinfo.value.paths == ["/rulemap/nodes/1/capabilities/0/payload/name"]


@pytest.mark.parametrize("parse", PARSE_FROM_EACH_FORM)
def test_rejects_what_only_the_mapping_checks(parse: Parse) -> None:
    # Arrange
    parser = RumlParser(extensions=[GreetingExtension()])
    document = greeting_document(
        {"salutation": "Hello"}, {"name": "world"}, declared=False
    )

    # Act / Assert
    with pytest.raises(ValueError, match="uses capabilities the root does not declare"):
        parse(parser, document)


def test_rejects_json_text_that_is_not_json() -> None:
    # Act / Assert
    with pytest.raises(json.JSONDecodeError):
        RumlParser().parse_json("{not json")
