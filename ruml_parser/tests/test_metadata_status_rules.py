# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§3.3.3: metadata statuses whose required fields the schema enforces — `inForce`
requires `validFrom`, `expired` requires `validUntil`, and
`replaced` requires `replacedBy`.
"""

import pytest

from ruml_parser.ruml_parser import RumlParser
from ruml_parser.schema_validation import RumlValidationError
from ruml_parser.tests.ruml_builders import (
    TIMESTAMP,
    minimal_metadata,
    node,
    ruml_document,
)

PARSER = RumlParser()

REPLACEMENT_ID = "9e107d9d-372e-4bfc-8d5a-826e0b7f2c11"

STATUS_REQUIREMENTS = [
    ("inForce", "validFrom", TIMESTAMP),
    ("expired", "validUntil", TIMESTAMP),
    ("replaced", "replacedBy", REPLACEMENT_ID),
]

# A leaf node has an operator only while the metadata status is `draft` (NODE-07), so
# the single node of these non-draft documents has none.
RULEMAP = {"nodes": {"1": node(operator=None)}}


@pytest.mark.parametrize(("status", "field", "_value"), STATUS_REQUIREMENTS)
def test_status_without_its_required_field_is_rejected(
    status: str, field: str, _value: str
) -> None:
    # Arrange
    metadata = minimal_metadata()
    metadata["status"] = status  # type: ignore[typeddict-item]
    document = ruml_document(metadata=metadata, rulemap=RULEMAP)

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(document)
    assert excinfo.value.paths == ["/metadata"]


@pytest.mark.parametrize(("status", "field", "value"), STATUS_REQUIREMENTS)
def test_status_with_its_required_field_passes(
    status: str, field: str, value: str
) -> None:
    # Arrange
    metadata = minimal_metadata()
    metadata["status"] = status  # type: ignore[typeddict-item]
    metadata[field] = value  # type: ignore[literal-required]
    document = ruml_document(metadata=metadata, rulemap=RULEMAP)

    # Act
    parsed = PARSER.parse_dict(document)

    # Assert
    assert parsed.metadata.status.value == status
