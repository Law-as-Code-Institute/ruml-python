# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§4.7.4: datapoint sets — the schema rule the schema enforces, and the
cross-object rules `to_internal()` checks (DP-16, DP-17).

The conformance cases in ruml-spec-tests cover the rest of the schema layer (a set
without fields, a valid set with an object datapoint).
"""

import pytest

from ruml_parser.internal.mapping import to_internal
from ruml_parser.model.ruml import RumlRulemappingLogicFormat
from ruml_parser.ruml_parser import RumlParser
from ruml_parser.schema_validation import RumlValidationError
from ruml_parser.tests.ruml_builders import capability, ruml_document
from ruml_parser.tests.ruml_dict import DatapointDict, DatapointSetDict

PARSER = RumlParser()


def string_datapoint() -> DatapointDict:
    return {"name": "Text", "type": "string", "binding": {"type": "input"}}


def object_datapoint(set_id: str) -> DatapointDict:
    return {
        "name": "Object",
        "type": "object",
        "set": set_id,
        "binding": {"type": "input"},
    }


def datapoint_set(fields: dict[str, DatapointDict]) -> DatapointSetDict:
    return {"name": "Set", "fields": fields}


def document(
    data: dict[str, DatapointDict], sets: dict[str, DatapointSetDict]
) -> RumlRulemappingLogicFormat:
    raw = ruml_document(
        capabilities=[capability("ruml:datapoints", {"data": data, "sets": sets})]
    )
    return RumlRulemappingLogicFormat.model_validate(raw)


def test_object_datapoint_without_a_set_is_rejected_by_the_schema() -> None:
    # Arrange
    datapoint: DatapointDict = {
        "name": "Object",
        "type": "object",
        "binding": {"type": "input"},
    }
    raw = ruml_document(
        capabilities=[capability("ruml:datapoints", {"data": {"dp_x": datapoint}})]
    )

    # Act / Assert
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(raw)
    assert excinfo.value.paths == ["/capabilities/0/payload/data/dp_x"]


def test_declared_and_nested_sets_pass() -> None:
    # Arrange: the address set nests the person set, and two datapoints share it
    parsed = document(
        data={
            "dp_home": object_datapoint("set_address"),
            "dp_work": object_datapoint("set_address"),
        },
        sets={
            "set_address": datapoint_set(
                {
                    "dp_street": string_datapoint(),
                    "dp_owner": object_datapoint("set_person"),
                }
            ),
            "set_person": datapoint_set({"dp_name": string_datapoint()}),
        },
    )

    # Act
    result = to_internal(parsed)

    # Assert
    assert result.capabilities.datapoints is not None
    assert result.capabilities.datapoints.sets.keys() == {"set_address", "set_person"}


def test_every_undeclared_set_reference_is_reported() -> None:
    # Arrange: a datapoint in `data` and a field of a set each name a missing set
    parsed = document(
        data={
            "dp_home": object_datapoint("set_address"),
            "dp_pet": object_datapoint("set_missing"),
        },
        sets={
            "set_address": datapoint_set(
                {
                    "dp_street": string_datapoint(),
                    "dp_owner": object_datapoint("set_nope"),
                }
            )
        },
    )

    # Act / Assert
    with pytest.raises(ValueError) as excinfo:
        to_internal(parsed)
    assert str(excinfo.value) == (
        "Some datapoints reference undeclared sets: "
        "datapoint 'dp_pet' -> set 'set_missing'; "
        "field 'dp_owner' of set 'set_address' -> set 'set_nope' "
        "(spec rule DP-16, chapter 4.7.4: an object datapoint's set resolves to an "
        "entry in sets)"
    )


def test_set_referencing_itself_is_rejected() -> None:
    # Arrange
    parsed = document(
        data={"dp_person": object_datapoint("set_person")},
        sets={
            "set_person": datapoint_set({"dp_partner": object_datapoint("set_person")})
        },
    )

    # Act / Assert
    with pytest.raises(ValueError) as excinfo:
        to_internal(parsed)
    assert str(excinfo.value) == (
        "Some sets reference themselves: set 'set_person': 'set_person' -> 'set_person' "
        "(spec rule DP-17, chapter 4.7.4: a set must not reference itself, directly or "
        "transitively)"
    )


def test_every_set_on_a_cycle_is_reported_with_its_chain() -> None:
    # Arrange: a -> b -> c -> b is a cycle through b and c, but not through a
    parsed = document(
        data={},
        sets={
            "set_a": datapoint_set({"dp_b": object_datapoint("set_b")}),
            "set_b": datapoint_set({"dp_c": object_datapoint("set_c")}),
            "set_c": datapoint_set({"dp_b": object_datapoint("set_b")}),
        },
    )

    # Act / Assert
    with pytest.raises(ValueError) as excinfo:
        to_internal(parsed)
    assert str(excinfo.value).startswith(
        "Some sets reference themselves: "
        "set 'set_b': 'set_b' -> 'set_c' -> 'set_b'; "
        "set 'set_c': 'set_c' -> 'set_b' -> 'set_c' "
    )


def test_sharing_a_set_is_not_recursion() -> None:
    # Arrange: a diamond — a nests b and c, both of which nest d
    parsed = document(
        data={"dp_a": object_datapoint("set_a")},
        sets={
            "set_a": datapoint_set(
                {"dp_b": object_datapoint("set_b"), "dp_c": object_datapoint("set_c")}
            ),
            "set_b": datapoint_set({"dp_d": object_datapoint("set_d")}),
            "set_c": datapoint_set({"dp_d": object_datapoint("set_d")}),
            "set_d": datapoint_set({"dp_leaf": string_datapoint()}),
        },
    )

    # Act
    result = to_internal(parsed)

    # Assert
    assert result.capabilities.datapoints is not None
    assert len(result.capabilities.datapoints.sets) == 4
