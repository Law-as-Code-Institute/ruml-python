# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""The `format` keywords of the RUML schema are asserted (CAP-28), e.g. DP-13 and CTX-03."""

from typing import Literal

import pytest

from ruml_parser.ruml_parser import RumlParser
from ruml_parser.schema_validation import _FORMAT_CHECKER, RumlValidationError
from ruml_parser.tests.ruml_builders import (
    TIMESTAMP,
    capability,
    minimal_metadata,
    ruml_document,
)
from ruml_parser.tests.ruml_dict import (
    ContextDict,
    DatapointDict,
    RumlRulemappingLogicFormatDict,
    ValidationDict,
)

PARSER = RumlParser()


@pytest.mark.parametrize(
    ("format_name", "value"),
    [
        ("date-time", "2026-08-20T12:00:00Z"),
        ("date-time", "2026-08-20t23:59:59.25-00:00"),
        ("date", "2024-02-29"),
        ("duration", "P2Y3M"),
        ("duration", "PT1H30M"),
        ("duration", "P1Y2D"),
        ("duration", "P4W"),
        ("uri", "https://www.gesetze-im-internet.de/bgb/__433.html"),
        ("uri", "urn:isbn:978-3-16-148410-0"),
        ("uri", "https://example.org/a%20b?q=1#frag"),
        ("uuid", "1A5B7C3D-2E4F-4A6B-8C9D-0E1F2A3B4C5D"),
        ("email", "jane.doe@example.org"),
        ("regex", r"^[1-9][0-9]*$"),
        ("regex", r"(?<year>\d{4})-\k<year>"),
        ("regex", r"^\p{Lu}\P{Lu}*$"),
        ("regex", r"\u{1F600}|\cJ"),
        ("regex", r"[^][]"),
        ("regex", r"[[(]"),
        ("regex", r"(?<=\d+)€"),
        ("regex", r"\k<missing>"),  # Annex B: `\k` without named groups is `k`
        ("regex", "a]"),
        ("regex", r"\p{NotAProperty}"),
        ("regex", "x{4294967296}"),
    ],
)
def test_a_valid_value_conforms(format_name: str, value: str) -> None:
    assert _FORMAT_CHECKER.conforms(value, format_name)


@pytest.mark.parametrize(
    ("format_name", "value"),
    [
        ("date-time", "2026-08-20T24:00:00Z"),  # no hour 24
        ("date-time", "2026-08-20T12:00:00+24:00"),
        ("date-time", "2016-12-31T23:59:60Z"),  # leap seconds are not supported
        ("date-time", "٢٠٢٦-08-20T12:00:00Z"),  # non-ASCII digits
        ("date", "2026-02-30"),
        ("date", "2026-2-3"),
        ("date", "20260203"),
        ("duration", "P"),
        ("duration", "PT"),
        ("duration", "P1Y2W"),
        ("duration", "1Y"),
        ("duration", "P0.5Y"),
        ("duration", "-P1D"),
        ("uri", "not a uri at all"),
        ("uri", "/relative/path"),
        ("uri", "https://example.org/a b"),
        ("uri", "https://example.org/%zz"),
        ("uuid", "1a5b7c3d2e4f4a6b8c9d0e1f2a3b4c5d"),
        ("uuid", "1a5b7c3d-2e4f-4a6b-8c9d-0e1f2a3b4c5"),
        ("email", "a@b@c"),
        ("email", "no-at-sign"),
        ("regex", "(["),
        ("regex", "a)"),
        ("regex", "\\"),
        ("regex", r"(?<a>x)\k<missing>"),
        ("regex", "(?P<n>x)"),
        ("regex", "(?i)abc"),
        ("regex", "a++"),
        ("regex", "(?>a)"),
        ("regex", "(" * 500 + ")" * 500),
        ("regex", "\ud800"),
    ],
)
def test_an_invalid_value_does_not_conform(format_name: str, value: str) -> None:
    assert not _FORMAT_CHECKER.conforms(value, format_name)


INVALID_VALUE_OF_EACH_FORMAT = {
    "date-time": "2026-08-20T24:00:00Z",
    "date": "2026-02-30",
    "time": "25:00:00Z",
    "duration": "PxD",
    "email": "a@b@c",
    "idn-email": "no-at-sign",
    "hostname": "a..b",
    "idn-hostname": "a..b",
    "ipv4": "256.0.0.1",
    "ipv6": "1:::2",
    "uri": "not a uri at all",
    "uri-reference": "http://exa mple.org",
    "iri": "not an iri",
    "iri-reference": "http://exa mple.org",
    "uuid": "1a5b7c3d2e4f4a6b8c9d0e1f2a3b4c5d",
    "uri-template": "{",
    "json-pointer": "a/b",
    "relative-json-pointer": "/a",
    "regex": "([",
}
"""Draft 2020-12's formats; jsonschema skips one whose package is missing."""


def test_every_format_of_draft_2020_12_has_a_check() -> None:
    assert set(_FORMAT_CHECKER.checkers) == set(INVALID_VALUE_OF_EACH_FORMAT)


@pytest.mark.parametrize(("format_name", "value"), INVALID_VALUE_OF_EACH_FORMAT.items())
def test_the_check_of_each_format_rejects(format_name: str, value: str) -> None:
    assert not _FORMAT_CHECKER.conforms(value, format_name)


@pytest.mark.parametrize(
    "pattern",
    [
        "a|" * 49_000 + "a",  # overflows regress's stack: SIGSEGV, not an exception
        "(a|" * 65 + "b" + ")" * 65,
        "x" * 1001,
    ],
)
def test_a_pattern_beyond_the_limits_is_rejected_without_compiling(
    pattern: str,
) -> None:
    assert not _FORMAT_CHECKER.conforms(pattern, "regex")


@pytest.mark.parametrize(
    "pattern",
    [
        "(" * 64 + ")" * 64,
        r"\(" * 100 + "[(((]" * 50,  # escaped or in a class: no nesting
        "a|" * 499 + "ab",
    ],
)
def test_a_pattern_within_the_limits_is_checked(pattern: str) -> None:
    assert _FORMAT_CHECKER.conforms(pattern, "regex")


def _datapoint_document(datapoint: DatapointDict) -> RumlRulemappingLogicFormatDict:
    return ruml_document(
        capabilities=[capability("ruml:datapoints", {"data": {"value": datapoint}})]
    )


def _context_document(context: ContextDict) -> RumlRulemappingLogicFormatDict:
    return ruml_document(
        capabilities=[capability("ruml:context", {"data": {"source": context}})]
    )


def _context(url: str, access_date: str | None = None) -> ContextDict:
    context: ContextDict = {
        "title": "Source",
        "category": "faq",
        "timestamp": TIMESTAMP,
        "url": url,
    }
    if access_date is not None:
        context["accessDate"] = access_date
    return context


def _datapoint(
    type_: Literal["string", "date", "duration"], validation: ValidationDict
) -> DatapointDict:
    return {
        "name": "Value",
        "type": type_,
        "binding": {"type": "input"},
        "validation": validation,
    }


def _metadata_with_email(email: str) -> RumlRulemappingLogicFormatDict:
    metadata = minimal_metadata()
    metadata["authors"] = [{"name": "Jane Doe", "email": email}]
    return ruml_document(metadata=metadata)


@pytest.mark.parametrize(
    ("document", "path"),
    [
        pytest.param(
            _datapoint_document(_datapoint("string", {"pattern": "(["})),
            "/capabilities/0/payload/data/value/validation/pattern",
            id="DP-13 regex",
        ),
        pytest.param(
            _datapoint_document(
                _datapoint("string", {"pattern": "(" * 500 + ")" * 500})
            ),
            "/capabilities/0/payload/data/value/validation/pattern",
            id="DP-13 regex nested too deeply",
        ),
        pytest.param(
            _datapoint_document(_datapoint("date", {"min": "2026-02-30"})),
            "/capabilities/0/payload/data/value/validation/min",
            id="date",
        ),
        pytest.param(
            _datapoint_document(_datapoint("duration", {"max": "18 years"})),
            "/capabilities/0/payload/data/value/validation/max",
            id="duration",
        ),
        pytest.param(
            _context_document(_context("not a uri at all")),
            "/capabilities/0/payload/data/source/url",
            id="CTX-03 uri",
        ),
        pytest.param(
            _metadata_with_email("a@b@c"),
            "/metadata/authors/0/email",
            id="email",
        ),
    ],
)
def test_a_value_of_the_wrong_format_is_reported_at_its_field(
    document: RumlRulemappingLogicFormatDict, path: str
) -> None:
    with pytest.raises(RumlValidationError) as excinfo:
        PARSER.parse_dict(document)
    assert excinfo.value.paths == [path]


@pytest.mark.parametrize(
    "document",
    [
        pytest.param(
            _datapoint_document(_datapoint("string", {"pattern": r"^(?<n>\d+)$"})),
            id="regex",
        ),
        pytest.param(
            _datapoint_document(_datapoint("date", {"min": "2024-02-29"})), id="date"
        ),
        pytest.param(
            _datapoint_document(_datapoint("duration", {"max": "P18Y"})),
            id="duration",
        ),
        pytest.param(
            _context_document(_context("https://example.org/x", "2026-08-20")),
            id="uri",
        ),
        pytest.param(_metadata_with_email("jane.doe@example.org"), id="email"),
    ],
)
def test_a_value_of_the_right_format_is_accepted(
    document: RumlRulemappingLogicFormatDict,
) -> None:
    PARSER.parse_dict(document)
