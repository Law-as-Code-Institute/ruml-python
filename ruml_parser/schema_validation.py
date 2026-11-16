# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Validation of RUML documents against ruml.schema.json and extensions' payload schemas."""

import json
import re
from collections.abc import Iterable, Mapping
from datetime import datetime
from functools import lru_cache
from typing import Any, Literal

import email_validator
import jsonschema
import regress
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from ruml_parser.internal.extension import CapabilityExtension
from ruml_parser.schema_files import SCHEMA_PATH


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    return _keep_paths_of_forbidden_properties(
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    )


def _keep_paths_of_forbidden_properties(schema: Any) -> Any:
    """Replace each property schema `false` with its equivalent `{"not": {}}`.

    jsonschema reports a `false` subschema's error without the property's path (its
    `descend()` takes a shortcut for boolean schemas that skips setting it), so the
    violation would be located at the object instead of at the forbidden property.
    """
    if isinstance(schema, list):
        return [_keep_paths_of_forbidden_properties(item) for item in schema]
    if not isinstance(schema, dict):
        return schema
    result = {
        key: _keep_paths_of_forbidden_properties(value) for key, value in schema.items()
    }
    for keyword in ("properties", "patternProperties"):
        if isinstance(result.get(keyword), dict):
            result[keyword] = {
                name: {"not": {}} if subschema is False else subschema
                for name, subschema in result[keyword].items()
            }
    return result


def ruml_validator(
    extensions: Iterable[CapabilityExtension] = (),
) -> jsonschema.protocols.Validator:
    """Build a validator of RUML documents that checks the payloads of ``extensions``.

    Building one is not cheap, so reuse it where possible, as ``RumlParser`` does.
    """
    extensions = tuple(extensions)
    schema = _extended_schema(extensions) if extensions else _schema()
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    resources: list[tuple[str, Mapping[str, Any]]] = [(_schema()["$id"], _schema())]
    for extension in extensions:
        schemas = extension.payload_schemas
        root = _keep_paths_of_forbidden_properties(schemas.root)
        node = _keep_paths_of_forbidden_properties(schemas.node)
        resources.append((_payload_schema_uri(extension, "root"), root))
        resources.append((_payload_schema_uri(extension, "node"), node))
    registry = Registry().with_resources(
        (uri, Resource.from_contents(contents, default_specification=DRAFT202012))
        for uri, contents in resources
    )
    return validator_cls(schema, registry=registry, format_checker=_FORMAT_CHECKER)


_RFC_3339_DATE_TIME = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt](?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]+)?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
)

_DURATION = re.compile(
    r"P(?!$)(?:[0-9]+Y)?(?:[0-9]+M)?(?:[0-9]+D)?(?:T(?=[0-9])(?:[0-9]+H)?(?:[0-9]+M)?(?:[0-9]+S)?)?"
    r"|P[0-9]+W"
)
"""RFC 3339 Appendix A durations, with the leniency of ajv-formats (`P1Y2D`)."""

_MAX_REGEX_LENGTH = 1000
_MAX_REGEX_NESTING = 64
"""Limits of a checkable pattern: beyond them `regress` can overflow a thread's stack,
which kills the process instead of raising."""

_FORMAT_CHECKER = jsonschema.FormatChecker(formats=())
"""Draft 2020-12's format checks, stricter for `date-time`, `duration` and `email`,
ECMA `regex`."""
_FORMAT_CHECKER.checkers.update(jsonschema.Draft202012Validator.FORMAT_CHECKER.checkers)


@_FORMAT_CHECKER.checks("date-time")
def _is_rfc_3339_date_time(value: object) -> bool:
    """Whether a string is an RFC 3339 date-time; an offset is mandatory there.

    Leap seconds (`23:59:60Z`) are rejected: a Python `datetime`, which the model holds
    timestamps as, cannot represent them.
    """
    if not isinstance(value, str):
        return True
    if not _RFC_3339_DATE_TIME.fullmatch(value):
        return False
    try:
        datetime.fromisoformat(value.upper())
    except ValueError:
        return False
    return True


@_FORMAT_CHECKER.checks("duration")
def _is_duration(value: object) -> bool:
    """Whether a string is a duration as the TypeScript parser accepts it.

    jsonschema's own check (isoduration) also takes fractions and signs (`P0.5Y`,
    `-P1D`), which RFC 3339 Appendix A does not.
    """
    return not isinstance(value, str) or _DURATION.fullmatch(value) is not None


@_FORMAT_CHECKER.checks("email")
def _is_email(value: object) -> bool:
    """Whether a string is an address the model's `EmailStr` accepts as well."""
    if not isinstance(value, str):
        return True
    try:
        email_validator.validate_email(value, check_deliverability=False)
    except email_validator.EmailNotValidError:
        return False
    return True


@_FORMAT_CHECKER.checks("regex")
def _is_ecma_262_regex(value: object) -> bool:
    """Whether a string is an ECMA-262 regular expression to `new RegExp(value)`.

    That is without the `u` flag, as the TypeScript parser checks it, so the syntax of
    Annex B is valid (`\\p` for `p`, a lone `]`). A string that `regress` cannot even
    take, one with a lone surrogate, is rejected, and so is a pattern longer than
    `_MAX_REGEX_LENGTH` or nested deeper than `_MAX_REGEX_NESTING`.
    """
    if not isinstance(value, str):
        return True
    if len(value) > _MAX_REGEX_LENGTH or _regex_nesting(value) > _MAX_REGEX_NESTING:
        return False
    try:
        regress.Regex(value)
    except Exception:
        return False
    return True


def _regex_nesting(pattern: str) -> int:
    """How deep the groups of ``pattern`` nest; brackets in a class or escaped don't count."""
    depth = deepest = 0
    escaped = in_class = False
    for char in pattern:
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif in_class:
            in_class = char != "]"
        elif char == "[":
            in_class = True
        elif char == "(":
            depth += 1
            deepest = max(deepest, depth)
        elif char == ")":
            depth = max(depth - 1, 0)
    return deepest


def _extended_schema(extensions: Iterable[CapabilityExtension]) -> dict[str, Any]:
    """Narrow the RUML schema to the payload schemas of ``extensions``.

    The extensions' schemas describe payloads only. Lifted to whole documents (by
    restating the path from the root down to the capability entries, and leaving
    everything else unconstrained), they combine with the RUML schema by ``allOf`` into
    a schema that a document satisfies if and only if it satisfies both.
    """
    root_rules: list[dict[str, Any]] = []
    node_rules: list[dict[str, Any]] = []
    for extension in extensions:
        root_uri = _payload_schema_uri(extension, "root")
        node_uri = _payload_schema_uri(extension, "node")
        root_rules.append(_payload_rule(extension.id, root_uri))
        node_rules.append(_payload_rule(extension.id, node_uri))
    lifted_node_rules = {
        "properties": {"capabilities": {"items": {"allOf": node_rules}}}
    }
    return {
        "$schema": _schema()["$schema"],
        "allOf": [
            {"$ref": _schema()["$id"]},
            {
                "properties": {
                    "capabilities": {"items": {"allOf": root_rules}},
                    "rulemap": {
                        "properties": {
                            "nodes": {"additionalProperties": lifted_node_rules}
                        }
                    },
                }
            },
        ],
    }


def _payload_rule(capability_id: str, payload_schema_uri: str) -> dict[str, Any]:
    """Build the schema rule picking a capability entry's payload schema by its id.

    The rule works the way the RUML schema's rules in ``CapabilityEntry`` and
    ``NodeCapabilityEntry`` do.
    """
    return {
        "if": {"required": ["id"], "properties": {"id": {"const": capability_id}}},
        "then": {"properties": {"payload": {"$ref": payload_schema_uri}}},
    }


def _payload_schema_uri(
    extension: CapabilityExtension, level: Literal["root", "node"]
) -> str:
    """Name the URI of one of ``extension``'s payload schemas in an extended schema."""
    return f"urn:ruml:capability-payload:{level}:{extension.id}"


def json_pointer(path: Iterable[Any]) -> str:
    """RFC 6901 JSON Pointer for a sequence of path segments."""

    def escape(segment: Any) -> str:
        return str(segment).replace("~", "~0").replace("/", "~1")

    return "".join(f"/{escape(segment)}" for segment in path)


def offending_path(error: jsonschema.exceptions.ValidationError) -> list[Any]:
    """`error.absolute_path`, extended to the specific key that offends.

    jsonschema reports `additionalProperties` and `propertyNames` failures
    against the *container* — the extra or malformed key itself, though it
    exists right there in the document, isn't part of `absolute_path`. Both
    keywords make the offending key identifiable, so append it: the key
    itself for `propertyNames` (`error.instance` *is* that key), and — for
    `additionalProperties` — whichever instance key matches neither
    `properties` nor `patternProperties` on the failing schema, the same
    computation `additionalProperties` itself does.
    """
    path: list[Any] = list(error.absolute_path)
    if (
        error.validator == "additionalProperties"
        and isinstance(error.schema, dict)
        and isinstance(error.instance, dict)
    ):
        allowed = set(error.schema.get("properties", {}))
        patterns = list(error.schema.get("patternProperties", {}))
        extra = sorted(
            key
            for key in error.instance
            if key not in allowed and not any(re.search(p, key) for p in patterns)
        )
        if extra:
            path.append(extra[0])
    elif "propertyNames" in error.schema_path:
        path.append(error.instance)
    return path


def _resolve(
    error: jsonschema.exceptions.ValidationError,
) -> jsonschema.exceptions.ValidationError:
    """Resolve one top-level error to the sub-error that best explains it.

    A plain keyword failure explains itself. A `oneOf`/`anyOf` failure does
    not — jsonschema's own `best_match()` over its branches can pick one
    that's wrong only because of its own discriminator (a `const`/`enum`
    mismatch) over a sibling branch that *is* the right variant and fails on
    something substantive. E.g. `binding: {type: "external"}` failing the
    `input` branch's `type == "input"` const is a worse explanation than
    failing the `external` branch's `required: [ref]`. Prefer the
    substantive branch when there is one.
    """
    if error.validator not in ("oneOf", "anyOf") or not error.context:
        return error
    candidate = jsonschema.exceptions.best_match(error.context)
    if candidate is None:
        return error
    if candidate.validator in ("const", "enum"):
        siblings = [e for e in error.context if e.validator not in ("const", "enum")]
        if siblings:
            candidate = jsonschema.exceptions.best_match(siblings) or candidate
    return candidate


def _drop_redundant_patterns(
    errors: list[jsonschema.exceptions.ValidationError],
) -> list[jsonschema.exceptions.ValidationError]:
    """Drop a `pattern` error when its subschema's `format` fails on the same value.

    The schema pairs some formats with a pattern that narrows them (`Uuid`: a
    lowercase v4 UUID); a value that is no UUID at all breaks both, and one error
    says enough.
    """

    def subschema(error: jsonschema.exceptions.ValidationError) -> tuple[Any, ...]:
        return (*error.absolute_path, "@", *list(error.absolute_schema_path)[:-1])

    failed_formats = {subschema(e) for e in errors if e.validator == "format"}
    return [
        error
        for error in errors
        if error.validator != "pattern" or subschema(error) not in failed_formats
    ]


def _message(error: jsonschema.exceptions.ValidationError) -> str:
    """Word the error; a forbidden property reads as it did before the rewrite."""
    if error.validator == "not" and error.validator_value == {}:
        return f"False schema does not allow {error.instance!r}"
    return error.message


class RumlValidationError(ValueError):
    """Raised by ``RumlParser`` when a document fails schema validation.

    A document can be invalid in more than one place at once, and a caller
    that only learns about one of them may "fix" it and resubmit only to
    be rejected again for a different, previously-hidden reason. This
    collects every independent violation `jsonschema` finds — resolved
    through `_resolve()` — and exposes their locations as JSON Pointers
    (`paths`) so callers — validation-test cases in particular — can check
    *where* the document was rejected, not just that it was.

    Rules the schema cannot express raise ``RumlStructuralError`` instead.
    """

    errors: list[jsonschema.exceptions.ValidationError]
    """The resolved `jsonschema` errors."""
    paths: list[str]
    """JSON Pointers of every offending location, sorted."""

    def __init__(self, causes: Iterable[jsonschema.exceptions.ValidationError]):
        self.errors = _drop_redundant_patterns([_resolve(cause) for cause in causes])
        super().__init__("; ".join(_message(error) for error in self.errors))
        self.paths = sorted(
            {json_pointer(offending_path(error)) for error in self.errors}
        )
