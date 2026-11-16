# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§2.5: identifier rules the schema enforces through the schema.

The conformance cases in ruml-spec-tests cover the rest (ids with capitals, upper-case
UUIDs, multi-segment third-party capability ids).
"""

from typing import Any

import pytest

from ruml_parser.ruml_parser import RumlParser
from ruml_parser.schema_validation import RumlValidationError
from ruml_parser.tests.ruml_builders import (
    capability,
    node_capability,
    node_with_capabilities,
    ruml_document,
)
from ruml_parser.tests.ruml_dict import DatapointDict

PARSER = RumlParser()


def datapoint() -> DatapointDict:
    return {"name": "Age", "type": "number", "binding": {"type": "input"}}


def test_kebab_case_datapoint_id_is_rejected() -> None:
    # Arrange: ids are snake_case so that they are plain JSONata names
    document = ruml_document(
        capabilities=[capability("ruml:datapoints", {"data": {"dp-age": datapoint()}})]
    )

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(document)
    assert excinfo.value.paths == ["/capabilities/0/payload/data/dp-age"]


@pytest.mark.parametrize(
    ("capability_id", "refs"),
    [
        ("ruml:context", ["ctx_ruling", "ctx_ruling"]),
        (
            "ruml:text-reference",
            [
                {"id": "text_bgb_823", "type": "refers-to"},
                {"id": "text_bgb_823", "type": "refers-to"},
            ],
        ),
    ],
)
def test_duplicate_refs_are_rejected(capability_id: str, refs: list[Any]) -> None:
    # Arrange
    document = node_with_capabilities(node_capability(capability_id, {"refs": refs}))

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(document)
    assert excinfo.value.paths == ["/rulemap/nodes/1/capabilities/0/payload/refs"]
