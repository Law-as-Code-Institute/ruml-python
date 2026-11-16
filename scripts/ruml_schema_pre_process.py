# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Schema rewrites applied to `ruml.schema.json` before code generation.

The schema's top-level `allOf` holds cross-field rules (`if`/`then` over the whole
document, such as "no node capabilities without root capabilities"), which
datamodel-code-generator cannot render into a model: it merges the rules' `properties`
into the root model as a duplicate, optional `rulemap` field. `RumlParser` enforces
the rules by validating against the real schema first. The same goes for the rule that
each official capability id occurs at most once per capability list.

The `if`/`then` rules *inside* the capability entry definitions, which pick a
payload's schema by the entry's id, are dropped by the codegen as well, typing
`payload` as a free-form object. For the Pydantic model that is what we want:
`to_internal()` narrows the payload by id. For the TypedDicts, which exist so that a
type checker can vet documents written as literals, a free-form payload would leave
the most error-prone part unchecked — so `pre_process_typed_dict` widens `payload` to
the union of the shapes those rules pick (see `widen_capability_payloads`).
"""

import json
from pathlib import Path
from typing import Any

CAPABILITY_ENTRIES = ("CapabilityEntry", "NodeCapabilityEntry")
"""The definitions whose `allOf` picks a payload schema by the entry's id."""


def drop_top_level_all_of(schema: dict[str, Any], schema_name: str) -> None:
    if schema.pop("allOf", None) is None:
        raise ValueError(f"{schema_name} has no top-level `allOf` to drop")


CAPABILITY_LISTS = ("Capabilities", "NodeCapabilities")
"""The definitions whose `allOf` caps each official capability id at one entry."""


def drop_capability_uniqueness_rules(schema: dict[str, Any]) -> None:
    """Drop the rule that each official capability id occurs at most once.

    It is a `contains`/`maxContains` check over the list, which the codegen renders as
    an empty model and puts in a union with the list type. `RumlParser` enforces it
    by validating against the real schema first.
    """
    for name in CAPABILITY_LISTS:
        del schema["$defs"][name]["allOf"]
    del schema["$defs"]["UniqueOfficialCapabilityIds"]


def drop_root_attrs_namespace(schema: dict[str, Any]) -> None:
    """Type the RUML Text root's attributes as the plain attribute map.

    Its required `xmlns` next to free attributes renders as `__pydantic_extra__`
    typed `Mapping`, which Pydantic rejects. `RumlParser` enforces `xmlns` by
    validating against the real schema first.
    """
    root_attrs = schema["$defs"]["RumlTextRootAttrs"]
    del root_attrs["properties"]
    del root_attrs["required"]


def widen_capability_payloads(schema: dict[str, Any]) -> None:
    """Retype each capability entry's `payload` as the union of its id rules' shapes.

    A closed TypedDict per shape means a payload with a misspelled or missing key
    matches none of them and is reported. The cost is that the id no longer picks the
    shape (any of the shapes goes with any id), and that a payload of a shape the
    rules do not know — a third-party or draft capability's — fails to type-check even
    though the schema allows it; such cases require a type-ignore comment or  `cast`.
    """
    for name in CAPABILITY_ENTRIES:
        definition = schema["$defs"][name]
        payload = definition["properties"]["payload"]
        payload["anyOf"] = [
            rule["then"]["properties"]["payload"]
            for rule in definition.pop("allOf")
            # Rules forbidding an id altogether (`then: false`, CAP-18) add no shape,
            # nor do those constraining another field (CAP-03 `role`, CAP-11
            # `required`).
            if isinstance(rule["then"], dict)
            and "payload" in (rule["then"].get("properties") or {})
        ]
        del payload["type"]  # `type: object` alongside `anyOf` would render as `dict`


# Entry points for this module by /scripts/update_models.py
def pre_process(ruml_schema_path: Path, target_path: Path) -> None:
    schema = json.loads(ruml_schema_path.read_text(encoding="utf-8"))
    drop_top_level_all_of(schema, ruml_schema_path.name)
    drop_capability_uniqueness_rules(schema)
    drop_root_attrs_namespace(schema)
    target_path.write_text(json.dumps(schema))


def pre_process_typed_dict(ruml_schema_path: Path, target_path: Path) -> None:
    schema = json.loads(ruml_schema_path.read_text(encoding="utf-8"))
    drop_top_level_all_of(schema, ruml_schema_path.name)
    drop_capability_uniqueness_rules(schema)
    widen_capability_payloads(schema)
    target_path.write_text(json.dumps(schema))
