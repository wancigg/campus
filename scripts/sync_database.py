"""将本地 SQLite 暂存数据增量同步到 MySQL。"""

import argparse
import os
import sys

# 允许直接 `python scripts/sync_database.py` 执行：把项目根加入 sys.path
_HERE = os.path.abspath(os.path.dirname(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, os.pardir))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from sqlalchemy import create_engine, insert, select, text
from sqlalchemy.exc import SQLAlchemyError

from config import Config, SQLITE_DB_PATH
from models import db


def _topological_tables(metadata):
    """按外键依赖顺序返回表，确保父表先写入。"""
    return list(metadata.sorted_tables)


def sync_sqlite_to_mysql(source_path, dry_run=False):
    if not os.path.exists(source_path):
        raise FileNotFoundError(f'找不到 SQLite 数据库：{source_path}')

    source = create_engine(f'sqlite:///{source_path}')
    target = create_engine(Config.MYSQL_DATABASE_URI, pool_pre_ping=True)

    try:
        with target.connect() as conn:
            conn.execute(text('SELECT 1'))

        db.metadata.create_all(target)
        table_names = [table.name for table in _topological_tables(db.metadata)]
        total_inserted = 0
        total_skipped = 0

        with source.connect() as source_conn, target.begin() as target_conn:
            for table in _topological_tables(db.metadata):
                rows = source_conn.execute(select(table)).mappings().all()
                if not rows:
                    continue

                target_columns = {column.name for column in table.columns}
                rows = [
                    {key: value for key, value in row.items() if key in target_columns}
                    for row in rows
                ]
                primary_key = list(table.primary_key.columns)

                for row in rows:
                    if primary_key:
                        pk_filter = [column == row[column.name] for column in primary_key]
                        exists = target_conn.execute(
                            select(table).where(*pk_filter).limit(1)
                        ).first()
                        if exists:
                            total_skipped += 1
                            continue
                    if dry_run:
                        total_inserted += 1
                    else:
                        target_conn.execute(insert(table).values(**row))
                        total_inserted += 1

        print(f'同步完成：新增 {total_inserted} 条，已存在跳过 {total_skipped} 条')
        if dry_run:
            print('当前为预览模式，MySQL 未写入任何数据。')
        print('同步表：' + ', '.join(table_names))
    except SQLAlchemyError as exc:
        raise RuntimeError(f'数据库同步失败，已回滚：{exc}') from exc
    finally:
        source.dispose()
        target.dispose()


def main():
    parser = argparse.ArgumentParser(description='将本地 SQLite 暂存数据同步到 MySQL')
    parser.add_argument(
        '--sqlite',
        default=SQLITE_DB_PATH,
        help=f'SQLite 数据库路径，默认：{SQLITE_DB_PATH}',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='只统计将要同步的数据，不写入 MySQL',
    )
    args = parser.parse_args()

    try:
        sync_sqlite_to_mysql(args.sqlite, dry_run=args.dry_run)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f'错误：{exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
