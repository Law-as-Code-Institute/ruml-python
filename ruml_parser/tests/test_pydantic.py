# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
import json
from collections.abc import Callable

import pytest
from pydantic import TypeAdapter, ValidationError
from pydantic_core import PydanticSerializationError

from ruml_parser.internal.mapping import to_internal
from ruml_parser.internal.ruml import RumlDocument
from ruml_parser.model.ruml import RumlRulemappingLogicFormat
from ruml_parser.pydantic import ParsedRumlDocument
from ruml_parser.tests.ruml_builders import (
    minimal_metadata,
    node,
    node_capability,
    ruml_document,
    unchecked_capability,
    unchecked_node_capability,
)
from ruml_parser.tests.ruml_dict import RumlRulemappingLogicFormatDict

ADAPTER = TypeAdapter[ParsedRumlDocument](ParsedRumlDocument)

type Validate = Callable[[RumlRulemappingLogicFormatDict], RumlDocument]
"""Hands a document to ``ADAPTER`` in one of the forms a field of the type accepts."""


def _validate_dict(document: RumlRulemappingLogicFormatDict) -> RumlDocument:
    return ADAPTER.validate_python(document)


def _validate_json(document: RumlRulemappingLogicFormatDict) -> RumlDocument:
    return ADAPTER.validate_json(json.dumps(document))


def _validate_model(document: RumlRulemappingLogicFormatDict) -> RumlDocument:
    return ADAPTER.validate_python(RumlRulemappingLogicFormat.model_validate(document))


VALIDATE_FROM_EACH_FORM = [
    pytest.param(_validate_dict, id="dict"),
    pytest.param(_validate_json, id="json"),
    pytest.param(_validate_model, id="model"),
]


def implicit_capability_document() -> RumlRulemappingLogicFormatDict:
    """A document whose node uses a capability, though the root declares none.

    The generated model accepts it: the schema forbids it by a top-level ``allOf`` rule,
    which code generation drops.
    """
    return ruml_document(
        rulemap={
            "nodes": {
                "1": node(
                    capabilities=[node_capability("ruml:query", {"expression": "$x"})]
                )
            }
        }
    )


@pytest.mark.parametrize("validate", VALIDATE_FROM_EACH_FORM)
def test_yields_the_internal_document(validate: Validate) -> None:
    # Arrange
    document = ruml_document()

    # Act
    result = validate(document)

    # Assert
    assert result == to_internal(RumlRulemappingLogicFormat.model_validate(document))


@pytest.mark.parametrize("validate", VALIDATE_FROM_EACH_FORM)
def test_rejects_what_only_the_schema_forbids(validate: Validate) -> None:
    # Arrange
    document = implicit_capability_document()
    RumlRulemappingLogicFormat.model_validate(document)  # the model alone accepts it

    # Act / Assert
    with pytest.raises(ValidationError) as excinfo:
        validate(document)
    [error] = excinfo.value.errors()
    assert (error["type"], error["loc"]) == (
        "ruml_schema",
        ("rulemap", "nodes", "1", "capabilities"),
    )


def test_reports_each_schema_violation_at_its_location() -> None:
    # Arrange
    document = implicit_capability_document()
    document["metadata"] = {**minimal_metadata(), "id": "not-a-uuid"}

    # Act / Assert
    with pytest.raises(ValidationError) as excinfo:
        ADAPTER.validate_python(document)
    assert sorted(
        (error["type"], error["loc"]) for error in excinfo.value.errors()
    ) == [
        ("ruml_schema", ("metadata", "id")),
        ("ruml_schema", ("rulemap", "nodes", "1", "capabilities")),
    ]


def test_a_structural_error_is_a_validation_error() -> None:
    # Arrange: valid by schema, but the node uses a capability the root lacks
    document = ruml_document(
        capabilities=[unchecked_capability("com.example/other", {}, role="data")],
        rulemap={
            "nodes": {
                "1": node(
                    capabilities=[unchecked_node_capability("com.example/greeting", {})]
                )
            }
        },
    )

    # Act / Assert
    with pytest.raises(ValidationError) as excinfo:
        ADAPTER.validate_python(document)
    [error] = excinfo.value.errors()
    assert error["type"] == "value_error"
    assert "uses capabilities the root does not declare" in error["msg"]


def test_has_the_json_schema_of_the_generated_model() -> None:
    # Act
    schema = ADAPTER.json_schema()

    # Assert
    assert schema == RumlRulemappingLogicFormat.model_json_schema()


def test_cannot_be_serialized() -> None:
    # Arrange
    result = ADAPTER.validate_python(ruml_document())

    # Act / Assert
    with pytest.raises(PydanticSerializationError, match="no mapping back to RUML"):
        ADAPTER.dump_python(result)
