import pytest

from app.core.errors import UnsafeSQLError
from app.services.sql_guard import validate

MAX = 1000


def test_simple_select_passes():
    out = validate("SELECT id, name FROM users", max_rows=MAX)
    assert "SELECT" in out.upper()
    assert "LIMIT" in out.upper()


def test_select_with_existing_limit_keeps_it():
    out = validate("SELECT * FROM users LIMIT 5", max_rows=MAX)
    assert "LIMIT 5" in out.upper().replace(" ", " ")


def test_select_with_cte_passes():
    sql = "WITH active AS (SELECT id FROM users WHERE active=true) SELECT count(*) FROM active"
    out = validate(sql, max_rows=MAX)
    assert "WITH" in out.upper()


def test_markdown_fences_are_stripped():
    sql = "```sql\nSELECT 1\n```"
    out = validate(sql, max_rows=MAX)
    assert "1" in out


def test_trailing_semicolon_is_tolerated():
    out = validate("SELECT 1;", max_rows=MAX)
    assert "1" in out


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE users",
        "DELETE FROM users WHERE id=1",
        "UPDATE users SET name='x' WHERE id=1",
        "INSERT INTO users (name) VALUES ('x')",
        "TRUNCATE users",
        "ALTER TABLE users ADD COLUMN x int",
        "CREATE TABLE x (id int)",
        "GRANT SELECT ON users TO public",
        "VACUUM users",
        "COPY users FROM '/tmp/x.csv'",
    ],
)
def test_forbidden_top_level_statements_are_rejected(sql):
    with pytest.raises(UnsafeSQLError):
        validate(sql, max_rows=MAX)


def test_multi_statement_is_rejected():
    with pytest.raises(UnsafeSQLError):
        validate("SELECT 1; SELECT 2;", max_rows=MAX)


def test_cte_with_dml_is_rejected():
    sql = "WITH d AS (DELETE FROM users RETURNING id) SELECT * FROM d"
    with pytest.raises(UnsafeSQLError):
        validate(sql, max_rows=MAX)


def test_empty_input_is_rejected():
    with pytest.raises(UnsafeSQLError):
        validate("", max_rows=MAX)
    with pytest.raises(UnsafeSQLError):
        validate("   \n  ", max_rows=MAX)


def test_unparseable_input_is_rejected():
    with pytest.raises(UnsafeSQLError):
        validate("this is not sql at all", max_rows=MAX)


def test_select_into_is_rejected():
    # SELECT ... INTO creates a new table, which we don't allow.
    with pytest.raises(UnsafeSQLError):
        validate("CREATE TABLE x AS SELECT * FROM users", max_rows=MAX)


def test_mixed_case_keywords_blocked():
    with pytest.raises(UnsafeSQLError):
        validate("DeLeTe FROM users", max_rows=MAX)
