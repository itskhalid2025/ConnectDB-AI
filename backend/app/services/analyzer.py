"""Post-execution analysis: choose a chart type and generate a Plotly spec.

We use simple heuristics over the column dtypes returned by Postgres rather
than asking the LLM to design the chart, because heuristics are deterministic,
fast, and good enough for the common analytical cases.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from app.schemas.chat import ChartSpec, TableResult


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_datetime_string(v: Any) -> bool:
    if not isinstance(v, str):
        return False
    # Heuristic: ISO-formatted dates/timestamps from sql_executor's coercion.
    try:
        dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
        return True
    except (ValueError, TypeError):
        return False


def _column_kind(rows: list[list[Any]], col_idx: int) -> str:
    """Return one of: 'number' | 'datetime' | 'category'."""
    sample = [r[col_idx] for r in rows if r[col_idx] is not None][:50]
    if not sample:
        return "category"
    if all(_is_number(v) for v in sample):
        return "number"
    if all(_is_datetime_string(v) or isinstance(v, dt.datetime) for v in sample):
        return "datetime"
    return "category"


def _column(rows: list[list[Any]], idx: int) -> list[Any]:
    return [r[idx] for r in rows]


def build_chart(table: TableResult, *, question: str = "") -> ChartSpec | None:
    """Pick a chart that fits the result shape, or return None for table-only."""
    if not table.columns or not table.rows:
        return None

    n_cols = len(table.columns)
    if n_cols < 2:
        return None

    kinds = [_column_kind(table.rows, i) for i in range(n_cols)]
    q_lower = question.lower()
    wants_pie = "pie" in q_lower
    wants_area = "area" in q_lower
    wants_heatmap = "heatmap" in q_lower or "heat map" in q_lower
    wants_horizontal = "horizontal" in q_lower or "row" in q_lower

    # 3-column Heatmap: Category, Category, Number
    if n_cols == 3 and (wants_heatmap or (kinds[0] == "category" and kinds[1] == "category" and kinds[2] == "number")):
        return _heatmap(table, x_idx=0, y_idx=1, z_idx=2)

    # 2-column shapes
    if n_cols == 2:
        a, b = kinds
        if a == "datetime" and b == "number":
            if wants_area:
                return _area(table, x_idx=0, y_idx=1)
            return _line(table, x_idx=0, y_indices=[1])
        if a == "category" and b == "number":
            if wants_pie or len(table.rows) <= 6:
                return _pie(table, label_idx=0, value_idx=1)
            return _bar(table, x_idx=0, y_idx=1, horizontal=wants_horizontal)
        if a == "number" and b == "number":
            return _scatter(table, x_idx=0, y_idx=1)
        return None

    # n_cols >= 3: multi-series logic
    axis_idx = next((i for i, k in enumerate(kinds) if k != "number"), None)
    if axis_idx is None:
        return None
    numeric_indices = [i for i, k in enumerate(kinds) if k == "number"]
    if not numeric_indices:
        return None

    if kinds[axis_idx] == "datetime":
        if wants_area:
            return _area(table, x_idx=axis_idx, y_idx=numeric_indices[0]) # Simplification for area
        return _line(table, x_idx=axis_idx, y_indices=numeric_indices)
    if kinds[axis_idx] == "category":
        return _multi_bar(table, x_idx=axis_idx, y_indices=numeric_indices)
    return None


def _heatmap(table: TableResult, *, x_idx: int, y_idx: int, z_idx: int) -> ChartSpec:
    x_data = list(dict.fromkeys(_column(table.rows, x_idx)))
    y_data = list(dict.fromkeys(_column(table.rows, y_idx)))
    
    z_matrix = [[None for _ in range(len(x_data))] for _ in range(len(y_data))]
    x_map = {val: i for i, val in enumerate(x_data)}
    y_map = {val: i for i, val in enumerate(y_data)}
    
    for row in table.rows:
        xi = x_map.get(row[x_idx])
        yi = y_map.get(row[y_idx])
        if xi is not None and yi is not None:
            z_matrix[yi][xi] = row[z_idx]

    data = [
        {
            "type": "heatmap",
            "x": x_data,
            "y": y_data,
            "z": z_matrix,
            "colorscale": "Viridis",
        }
    ]
    layout = {
        "xaxis": {"title": table.columns[x_idx]},
        "yaxis": {"title": table.columns[y_idx]},
        "margin": {"l": 50, "r": 20, "t": 20, "b": 50},
    }
    return ChartSpec(data=data, layout=layout)


def _pie(table: TableResult, *, label_idx: int, value_idx: int) -> ChartSpec:
    data = [
        {
            "type": "pie",
            "labels": _column(table.rows, label_idx),
            "values": _column(table.rows, value_idx),
            "hole": 0.4,
            "textinfo": "label+percent",
        }
    ]
    layout = {
        "showlegend": True,
        "margin": {"l": 20, "r": 20, "t": 20, "b": 20},
    }
    return ChartSpec(data=data, layout=layout)


def _area(table: TableResult, *, x_idx: int, y_idx: int) -> ChartSpec:
    data = [
        {
            "type": "scatter",
            "mode": "lines",
            "name": table.columns[y_idx],
            "x": _column(table.rows, x_idx),
            "y": _column(table.rows, y_idx),
            "fill": "tozeroy",
        }
    ]
    layout = {
        "xaxis": {"title": table.columns[x_idx]},
        "yaxis": {"title": table.columns[y_idx]},
        "margin": {"l": 50, "r": 20, "t": 20, "b": 50},
    }
    return ChartSpec(data=data, layout=layout)


def _line(table: TableResult, *, x_idx: int, y_indices: list[int]) -> ChartSpec:
    x = _column(table.rows, x_idx)
    data = [
        {
            "type": "scatter",
            "mode": "lines+markers",
            "name": table.columns[i],
            "x": x,
            "y": _column(table.rows, i),
        }
        for i in y_indices
    ]
    layout = {
        "xaxis": {"title": table.columns[x_idx]},
        "yaxis": {"title": table.columns[y_indices[0]] if len(y_indices) == 1 else "value"},
        "margin": {"l": 50, "r": 20, "t": 20, "b": 50},
    }
    return ChartSpec(data=data, layout=layout)


def _bar(table: TableResult, *, x_idx: int, y_idx: int, horizontal: bool = False) -> ChartSpec:
    data = [
        {
            "type": "bar",
            "name": table.columns[y_idx],
            "x": _column(table.rows, x_idx) if not horizontal else _column(table.rows, y_idx),
            "y": _column(table.rows, y_idx) if not horizontal else _column(table.rows, x_idx),
            "orientation": "h" if horizontal else "v",
        }
    ]
    layout = {
        "xaxis": {"title": table.columns[x_idx] if not horizontal else table.columns[y_idx]},
        "yaxis": {"title": table.columns[y_idx] if not horizontal else table.columns[x_idx]},
        "margin": {"l": 100 if horizontal else 50, "r": 20, "t": 20, "b": 50},
    }
    return ChartSpec(data=data, layout=layout)


def _multi_bar(table: TableResult, *, x_idx: int, y_indices: list[int]) -> ChartSpec:
    x = _column(table.rows, x_idx)
    data = [
        {
            "type": "bar",
            "name": table.columns[i],
            "x": x,
            "y": _column(table.rows, i),
        }
        for i in y_indices
    ]
    layout = {
        "barmode": "group",
        "xaxis": {"title": table.columns[x_idx]},
        "yaxis": {"title": "value"},
        "margin": {"l": 50, "r": 20, "t": 20, "b": 50},
    }
    return ChartSpec(data=data, layout=layout)


def _scatter(table: TableResult, *, x_idx: int, y_idx: int) -> ChartSpec:
    data = [
        {
            "type": "scatter",
            "mode": "markers",
            "name": table.columns[y_idx],
            "x": _column(table.rows, x_idx),
            "y": _column(table.rows, y_idx),
        }
    ]
    layout = {
        "xaxis": {"title": table.columns[x_idx]},
        "yaxis": {"title": table.columns[y_idx]},
        "margin": {"l": 50, "r": 20, "t": 20, "b": 50},
    }
    return ChartSpec(data=data, layout=layout)


def _multi_bar(table: TableResult, *, x_idx: int, y_indices: list[int]) -> ChartSpec:
    x = _column(table.rows, x_idx)
    data = [
        {
            "type": "bar",
            "name": table.columns[i],
            "x": x,
            "y": _column(table.rows, i),
        }
        for i in y_indices
    ]
    layout = {
        "barmode": "group",
        "xaxis": {"title": table.columns[x_idx]},
        "yaxis": {"title": "value"},
        "margin": {"l": 50, "r": 20, "t": 20, "b": 50},
    }
    return ChartSpec(data=data, layout=layout)


def _scatter(table: TableResult, *, x_idx: int, y_idx: int) -> ChartSpec:
    data = [
        {
            "type": "scatter",
            "mode": "markers",
            "name": table.columns[y_idx],
            "x": _column(table.rows, x_idx),
            "y": _column(table.rows, y_idx),
        }
    ]
    layout = {
        "xaxis": {"title": table.columns[x_idx]},
        "yaxis": {"title": table.columns[y_idx]},
        "margin": {"l": 50, "r": 20, "t": 20, "b": 50},
    }
    return ChartSpec(data=data, layout=layout)
