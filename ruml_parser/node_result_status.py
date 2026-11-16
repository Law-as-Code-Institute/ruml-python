# SPDX-FileCopyrightText: 2026 Rulemapping Group GmbH
# SPDX-License-Identifier: Apache-2.0
"""The statuses a node result of a RUML-Result document can have.

Hand-written because the RUML-Result schema has no enum of the statuses: each one
selects its own result shape (`TrueResult`, ..., `IgnoredResult` in
`ruml_parser.model.ruml_result`), whose `status` is a constant.
"""

from enum import StrEnum


class NodeResultStatus(StrEnum):
    """Final evaluated status of a node; `pending` nodes are omitted from results."""

    true = "true"
    false = "false"
    undefined = "undefined"
    ignored = "ignored"
