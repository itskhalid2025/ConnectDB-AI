"""
File: schema_builder.py
Version: 1.0.0
Created At: 2026-04-29
Description: Utility for formatting database schema metadata into LLM-optimized 
             context strings. Enhances schema_inspector output with additional hints.
"""

from app.schemas.connection import SchemaSummary

def build_schema_context(summary: SchemaSummary) -> str:
    """
    Renders a compact but detailed schema representation for the LLM.
    Includes tables, columns, types, and foreign key relationships.
    """
    lines = []
    for table in summary.tables:
        # Format: table_name (col1:type, col2:type)
        cols = [f"{c.name}:{c.data_type}" for c in table.columns]
        table_line = f"- {table.name} ({', '.join(cols)})"
        
        # Add Foreign Key hints: [FKs: col -> ref_table.ref_col]
        if table.foreign_keys:
            fks = [
                f"{fk.column} -> {fk.references_table}.{fk.references_column}"
                for fk in table.foreign_keys
            ]
            table_line += f" [FKs: {'; '.join(fks)}]"
        
        # Add approximate row counts for scale awareness
        if table.approx_row_count is not None:
            table_line += f" (~{table.approx_row_count} rows)"
            
        lines.append(table_line)
        
    return "\n".join(lines) if lines else "(No tables found in schema)"
