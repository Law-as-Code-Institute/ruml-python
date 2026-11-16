# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""The spec's rules on datapoint sets (chapter 4.7.4, rules DP-16 and DP-17)."""

from collections import deque
from collections.abc import Iterator

from more_itertools import unique_everseen

from ruml_parser.internal.ruml import (
    Datapoint,
    DatapointsCapabilityDeclaration,
    DatapointSet,
    RumlDocument,
    SetId,
)


def reject_undeclared_set_references(document: RumlDocument) -> None:
    """Raise if a datapoint names a set the document does not declare (DP-16).

    Every `set` a datapoint carries — in `data` as well as among the `fields` of a set
    — must be an id declared in `sets` (spec chapter 4.7.4). The schema cannot relate
    a datapoint's `set` to the keys of `sets`, so the rule is checked here; all
    offending datapoints are reported at once.

    Raises:
        ValueError: Naming every offending datapoint and the set it references.
    """
    datapoints = document.capabilities.datapoints
    if datapoints is None:
        return
    offences = [
        f"{location} -> set {datapoint.set!r}"
        for location, datapoint in _set_references(datapoints)
        if datapoint.set not in datapoints.sets
    ]
    if offences:
        raise ValueError(
            "Some datapoints reference undeclared sets: "
            + "; ".join(offences)
            + " (spec rule DP-16, chapter 4.7.4: an object datapoint's set resolves "
            "to an entry in sets)"
        )


def reject_recursive_sets(document: RumlDocument) -> None:
    """Raise if a set references itself, directly or transitively (DP-17).

    A field of a set may itself be of type `object` (nesting), but the sets must not
    form a cycle (spec chapter 4.7.4): an instance would have no end. Every set on a
    cycle is reported, each with the shortest chain of references leading back to it.
    A reference to an undeclared set is `reject_undeclared_set_references`' business
    and does not count as an edge here.

    Raises:
        ValueError: Naming every offending set and the chain of references that leads
            back to it.
    """
    datapoints = document.capabilities.datapoints
    if datapoints is None:
        return
    references = {
        set_id: _referenced_sets(set_) for set_id, set_ in datapoints.sets.items()
    }
    offences = [
        f"set {set_id!r}: " + " -> ".join(repr(set_id) for set_id in cycle)
        for set_id in references
        if (cycle := _cycle_through(set_id, references)) is not None
    ]
    if offences:
        raise ValueError(
            "Some sets reference themselves: "
            + "; ".join(offences)
            + " (spec rule DP-17, chapter 4.7.4: a set must not reference itself, "
            "directly or transitively)"
        )


def _set_references(
    datapoints: DatapointsCapabilityDeclaration,
) -> Iterator[tuple[str, Datapoint]]:
    """Yield every datapoint that carries a `set`, with a description of where it is."""
    for datapoint_id, datapoint in datapoints.data.items():
        if datapoint.set is not None:
            yield f"datapoint {datapoint_id!r}", datapoint
    for set_id, set_ in datapoints.sets.items():
        for datapoint_id, datapoint in set_.fields.items():
            if datapoint.set is not None:
                yield f"field {datapoint_id!r} of set {set_id!r}", datapoint


def _referenced_sets(set_: DatapointSet) -> list[SetId]:
    """Return the distinct sets the fields of `set_` reference, in field order."""
    return list(
        unique_everseen(
            field.set for field in set_.fields.values() if field.set is not None
        )
    )


def _cycle_through(
    start: SetId, references: dict[SetId, list[SetId]]
) -> list[SetId] | None:
    """Return the shortest chain of references from `start` back to itself.

    Returns `None` if there is none.

    A breadth-first search over `references`; the chain begins and ends with `start`,
    so a set referencing itself directly yields `[start, start]`.
    """
    parents: dict[SetId, SetId] = {}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        for referenced in references.get(current, ()):
            if referenced == start:
                chain = [current]
                while chain[-1] != start:
                    chain.append(parents[chain[-1]])
                return [*reversed(chain), start]
            if referenced not in parents:
                parents[referenced] = current
                queue.append(referenced)
    return None
