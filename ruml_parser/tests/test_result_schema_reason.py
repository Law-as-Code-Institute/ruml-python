# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""§5.1: a node result's `status` decides the shape of its (required) `reason`.

The RUML-Result schema is not validated at runtime anywhere in this repo (the
evaluator builds results through the generated pydantic model), so these tests
check the schema file itself — it is the published contract.
"""

import json
from collections.abc import Mapping
from typing import Any

import jsonschema
import pytest

from ruml_parser.schema_files import RESULT_SCHEMA_PATH
from ruml_parser.tests.ruml_result_dict import (
    IgnoredReasonDict,
    NodeResultDict,
    UndefinedReasonDict,
)

SCHEMA = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))

IGNORED_REASON: IgnoredReasonDict = {
    "type": "shortCircuit",
    "trigger": "71946db2-13e2-49df-9f7b-59369cff7679",
    "operator": "AND",
    "mode": "optimized",
}

UNDEFINED_REASON: UndefinedReasonDict = {"type": "default", "message": "no result"}


def result_document(node_result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "$format": "RUML-Result",
        "$specVersion": "1.0",
        "rumlReference": {"id": "0257de51-c3c1-45c2-be5f-602869770d86"},
        "evaluation": {
            "id": "39d467ac-8e6a-4fa5-bb36-eebbf6aec1a7",
            "timestamp": "2026-08-20T12:00:00.000Z",
            "mode": "optimized",
            "results": {"1": node_result},
        },
    }


def validate(document: Mapping[str, Any]) -> list[str]:
    validator_cls = jsonschema.validators.validator_for(SCHEMA)
    return [error.message for error in validator_cls(SCHEMA).iter_errors(document)]


@pytest.mark.parametrize(
    "node_result",
    [
        {"lexId": "1", "status": "true", "reason": "it holds"},
        {"lexId": "1", "status": "false", "reason": "it does not hold"},
        {"lexId": "1", "status": "undefined", "reason": UNDEFINED_REASON},
        {"lexId": "1", "status": "ignored", "reason": IGNORED_REASON},
    ],
    ids=["true", "false", "undefined", "ignored"],
)
def test_reason_of_the_status_shape_is_valid(node_result: NodeResultDict) -> None:
    assert validate(result_document(node_result)) == []


@pytest.mark.parametrize("status", ["true", "false", "undefined", "ignored"])
def test_missing_reason_is_rejected(status: str) -> None:
    document = result_document({"lexId": "1", "status": status})
    assert validate(document) != []


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        ("true", IGNORED_REASON),
        ("undefined", "no result"),
        ("ignored", "short-circuit"),
    ],
)
def test_reason_of_another_shape_is_rejected(status: str, reason: object) -> None:
    document = result_document({"lexId": "1", "status": status, "reason": reason})
    assert validate(document) != []


def test_former_ignored_reason_field_is_rejected() -> None:
    document = result_document(
        {
            "lexId": "1",
            "status": "ignored",
            "reason": IGNORED_REASON,
            "ignoredReason": IGNORED_REASON,
        }
    )
    assert validate(document) != []
