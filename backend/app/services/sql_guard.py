"""SQL safety validator.

We only permit read-only operations. The strategy is defence-in-depth:
1. Strip any markdown fences the LLM might emit.
2. Parse with sqlglot.
3. Reject if the input contains more than one statement.
4. Reject if the root expression is anything other than SELECT or WITH (CTE → SELECT).
5. Walk the AST and reject if any forbidden node type appears anywhere
   (defends against `WITH x AS (DELETE ...) SELECT ...`).
6. Inject a LIMIT clause if the outermost SELECT is missing one.
"""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

from app.core.errors import UnsafeSQLError

# Anything that mutates state, alters schema, manages users, or escapes the SQL
# context is forbidden. These are checked anywhere in the AST tree.
# We use a dynamic list to avoid AttributeErrors across different sqlglot versions.
_FORBIDDEN_NODE_NAMES = [
    "Insert",
    "Update",
    "Delete",
    "Drop",
    "Alter",
    "AlterTable",
    "AlterColumn",
    "Create",
    "Truncate",
    "TruncateTable",
    "Grant",
    "Merge",
    "Command",  # catches generic commands like COPY, VACUUM, SET
]
FORBIDDEN_NODE_TYPES: tuple[type[exp.Expression], ...] = tuple(
    getattr(exp, name) for name in _FORBIDDEN_NODE_NAMES if hasattr(exp, name)
)

# Statement starters we explicitly block via raw text inspection as a belt-and-braces
# check, before sqlglot has had a chance to interpret anything.
_FORBIDDEN_KEYWORDS_RE = re.compile(
    r"\b(?:insert|update|delete|drop|alter|create|truncate|grant|revoke|"
    r"merge|copy|vacuum|reindex|cluster|comment|lock|call|execute|do)\b",
    re.IGNORECASE,
)


def _strip_fences(sql: str) -> str:
    """LLMs sometimes wrap SQL in ```sql fences despite being told not to."""
    s = sql.strip()
    if s.startswith("```"):
        # remove first fence line
        s = s.split("\n", 1)[1] if "\n" in s else s.lstrip("`")
        if s.endswith("```"):
            s = s[: -3]
    return s.strip().rstrip(";").strip()


def _has_limit(node: exp.Expression) -> bool:
    return node.args.get("limit") is not None


def _inject_limit(tree: exp.Expression, max_rows: int) -> exp.Expression:
    """Add a LIMIT to the outermost SELECT if missing, leaving CTEs alone."""
    target = tree
    if isinstance(tree, exp.With):
        # Walk down to the wrapped SELECT/UNION
        target = tree.this
    if isinstance(target, (exp.Select, exp.Union)) and not _has_limit(target):
        target.set("limit", exp.Limit(expression=exp.Literal.number(max_rows)))
    return tree


def validate(sql: str, *, max_rows: int) -> str:
    """Validate `sql`, raise UnsafeSQLError on rejection, return the safe form."""
    if not sql or not sql.strip():
        raise UnsafeSQLError("Empty SQL.", hint="The model didn't return a query — try rephrasing.")

    cleaned = _strip_fences(sql)

    # Coarse keyword scan first — fast and catches obvious stuff before parsing.
    if _FORBIDDEN_KEYWORDS_RE.search(cleaned):
        raise UnsafeSQLError(
            "Generated SQL contains a forbidden operation.",
            hint="I can only run read-only SELECT queries against your database.",
        )

    try:
        statements = sqlglot.parse(cleaned, read="postgres")
    except Exception as e:  # sqlglot raises ParseError but also bare exceptions
        raise UnsafeSQLError(
            f"Could not parse generated SQL: {e}",
            hint="The model produced invalid SQL — try rephrasing your question.",
        ) from e

    statements = [s for s in statements if s is not None]
    if len(statements) == 0:
        raise UnsafeSQLError("No statements parsed.", hint="Try rephrasing your question.")
    if len(statements) > 1:
        raise UnsafeSQLError(
            "Only a single SQL statement is allowed.",
            hint="The model returned multiple statements — try a more specific question.",
        )

    tree = statements[0]

    # The root must be SELECT, UNION, or WITH (which wraps a SELECT/UNION).
    if isinstance(tree, exp.With):
        wrapped = tree.this
        if not isinstance(wrapped, (exp.Select, exp.Union)):
            raise UnsafeSQLError(
                "Only SELECT queries are allowed.",
                hint="I can only run read queries — your request seemed to ask for something else.",
            )
    elif not isinstance(tree, (exp.Select, exp.Union)):
        raise UnsafeSQLError(
            "Only SELECT queries are allowed.",
            hint="I can only run read queries — your request seemed to ask for something else.",
        )

    # Walk the entire tree; any forbidden node anywhere = reject.
    for node in tree.walk():
        # `walk` yields tuples in some sqlglot versions; normalise to the node.
        candidate = node[0] if isinstance(node, tuple) else node
        if isinstance(candidate, FORBIDDEN_NODE_TYPES):
            raise UnsafeSQLError(
                f"Generated SQL contains a forbidden operation: {type(candidate).__name__}.",
                hint="I can only run read-only SELECT queries.",
            )

    safe_tree = _inject_limit(tree, max_rows)
    return safe_tree.sql(dialect="postgres")
