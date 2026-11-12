"""轻量级启动期 schema 补齐。

本批次沿用 Base.metadata.create_all() 完成首次建表，但 create_all 不会给
已存在的表追加新列。为兼容带历史数据卷的部署，这里幂等检查并 ALTER 缺失列；
新表仍由 create_all 创建。正式生产演进应替换为 Alembic 迁移。
"""
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

# (表名, 列名, 列 DDL) —— JSON 在 SQLite 下按 TEXT 存储、Postgres 下为 json。
_MISSING_COLUMNS = [
    ("analysis_runs", "rule_fingerprint", "VARCHAR(64) DEFAULT ''"),
    ("analysis_runs", "review_sync", "JSON DEFAULT '{}'"),
]


def ensure_columns(engine: Engine) -> list[str]:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    applied: list[str] = []
    with engine.begin() as conn:
        for table, column, ddl in _MISSING_COLUMNS:
            if table not in existing_tables:
                continue  # 整表缺失时交给 create_all 统一创建
            present = {col["name"] for col in inspector.get_columns(table)}
            if column not in present:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))
                applied.append(f"{table}.{column}")
    return applied
