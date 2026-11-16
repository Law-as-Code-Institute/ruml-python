# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Where `RumlValidationError` reports a violation jsonschema locates imprecisely."""

import pytest
from pydantic import TypeAdapter, ValidationError

from ruml_parser.pydantic import ParsedRumlDocument
from ruml_parser.ruml_parser import RumlParser
from ruml_parser.schema_validation import RumlValidationError
from ruml_parser.tests.ruml_builders import (
    minimal_metadata,
    node,
    ruml_document,
)
from ruml_parser.tests.ruml_dict import RumlRulemappingLogicFormatDict

PARSER = RumlParser()

CHILD_ID = "1a5b7c3d-2e4f-4a6b-8c9d-0e1f2a3b4c5d"


def test_an_operator_on_a_leaf_outside_a_draft_is_reported_at_the_operator() -> None:
    # Arrange: NODE-07 forbids the property itself (`operator: false`)
    metadata = minimal_metadata()
    metadata["status"] = "review"
    document = ruml_document(
        metadata=metadata,
        rulemap={
            "nodes": {
                "1": node(operator="AND", children=["2"]),
                "2": node(id=CHILD_ID, label="leaf", operator="OR"),
            }
        },
    )

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(document)
    assert excinfo.value.paths == ["/rulemap/nodes/2/operator"]
    assert str(excinfo.value) == "False schema does not allow 'OR'"


def _leaf_with_operator_equal_to_its_label() -> RumlRulemappingLogicFormatDict:
    """NODE-07 broken by a leaf whose `label` is the same (interned) string as `operator`."""
    metadata = minimal_metadata()
    metadata["status"] = "review"
    return ruml_document(
        metadata=metadata,
        rulemap={
            "nodes": {
                "1": node(operator="AND", children=["2"]),
                "2": node(id=CHILD_ID, label="AND", operator="AND"),
            }
        },
    )


def test_a_forbidden_operator_equal_to_another_field_is_reported_at_the_operator() -> (
    None
):
    # Arrange
    document = _leaf_with_operator_equal_to_its_label()

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(document)
    assert excinfo.value.paths == ["/rulemap/nodes/2/operator"]


def test_a_pydantic_field_reports_a_forbidden_operator_at_the_operator() -> None:
    # Arrange
    document = _leaf_with_operator_equal_to_its_label()

    # Act / Assert
    with pytest.raises(ValidationError) as excinfo:
        TypeAdapter[ParsedRumlDocument](ParsedRumlDocument).validate_python(document)
    assert [error["loc"] for error in excinfo.value.errors()] == [
        ("rulemap", "nodes", "2", "operator")
    ]


def test_node_capabilities_without_root_capabilities_are_reported_at_the_list() -> None:
    # Arrange: CAP-14 forbids the property itself (`capabilities: false`)
    document = ruml_document(rulemap={"nodes": {"1": node(capabilities=[])}})

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(document)
    assert excinfo.value.paths == ["/rulemap/nodes/1/capabilities"]


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-08-20T12:00:00",  # no offset
        "2026-08-20 12:00:00Z",  # no `T`
        "2026-08-20",  # no time
        "2026-02-30T12:00:00Z",  # no such day
        "2026-08-20T24:00:00Z",  # no hour 24
        "2016-12-31T23:59:60Z",  # a leap second, which a `datetime` cannot hold
    ],
)
def test_a_timestamp_that_is_no_rfc_3339_date_time_is_reported_at_its_field(
    timestamp: str,
) -> None:
    # Arrange
    metadata = minimal_metadata()
    metadata["created"] = timestamp
    document = ruml_document(metadata=metadata)

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(document)
    assert excinfo.value.paths == ["/metadata/created"]


@pytest.mark.parametrize(
    "timestamp",
    ["2026-08-20T12:00:00Z", "2026-08-20T12:00:00.25+02:00", "2026-08-20t12:00:00z"],
)
def test_an_rfc_3339_date_time_is_accepted(timestamp: str) -> None:
    # Arrange
    metadata = minimal_metadata()
    metadata["created"] = timestamp
    metadata["modified"] = timestamp
    document = ruml_document(metadata=metadata)

    # Act
    parsed = PARSER.parse_dict(document)

    # Assert
    assert parsed.metadata.created.tzinfo is not None
