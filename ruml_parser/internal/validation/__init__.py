# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""Additional validations to apply while building internal model instances.

For now, contains the spec's cross-object rules: The schema validates one object at a
time and the dataclasses carry no validation, so a rule that relates different parts of
a document (e.g. a node's capability ids to the root's declarations) is checked here
instead, one module per rule (or family of rules).
Most of them raise, and `ruml_parser.internal.mapping.to_internal` is meant to run those
on the document it has just built, so that a `RumlDocument` obtained from it satisfies
them. `recursion` is the partial exception: §6.4 asks an implementation to *warn* about
some of what it finds rather than reject the document, so its validation logs those
findings as warnings and raises only for the chapter's `MUST`/`MUST NOT` rules.
"""
