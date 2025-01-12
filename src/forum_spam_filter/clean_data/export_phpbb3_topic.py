"""
Connects to a phpBB3 database (only MariaDB is supported, for now)
and exports a topic to a CSV file containing a label (either ham or
spam).

This assumes you have a topic in a phpBB3 forum that is either all
spam or all ham. You can then use this CSV file as additional training
data for your model.
"""

import os
import csv
import getpass
import sys
import mariadb
import argparse
import typing
from .util import LABEL_MAP


def export_phpbb3_forum(
    output: typing.TextIO,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    table_prefix: str,
    forum_id: int,
    label: str,
) -> None:
    writer = csv.DictWriter(
        output,
        fieldnames=["text", "label"],
        quoting=csv.QUOTE_MINIMAL,
        lineterminator=os.linesep,
        delimiter=",",
        quotechar='"',
        escapechar="\\",
    )
    conn = mariadb.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        reconnect=True,
        unix_socket=None,
        ssl_verify_cert=False,
    )
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            SELECT
                p.post_text AS text,
                {LABEL_MAP[label]} AS label
            FROM {table_prefix}posts p
            JOIN {table_prefix}topics t ON p.topic_id = t.topic_id
            WHERE t.forum_id = ?
            AND p.post_visibility = 1
            ORDER BY p.post_time
            """,
            (forum_id,),
        )
        for row in cursor:
            writer.writerow({"text": row[0], "label": row[1]})
    finally:
        cursor.close()
        conn.close()


def export_phpbb3_topic(
    output: typing.TextIO,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    table_prefix: str,
    topic_id: int,
    label: str,
) -> None:
    writer = csv.DictWriter(
        output,
        fieldnames=["text", "label"],
        quoting=csv.QUOTE_MINIMAL,
        lineterminator=os.linesep,
        delimiter=",",
        quotechar='"',
        escapechar="\\",
    )
    conn = mariadb.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        reconnect=True,
        unix_socket=None,
        ssl_verify_cert=False,
    )
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            SELECT
                p.post_text AS text,
                {LABEL_MAP[label]} AS label
            FROM {table_prefix}posts p
            WHERE p.topic_id = ?
            ORDER BY p.post_time
            """,
            (topic_id,),
        )
        for row in cursor:
            writer.writerow({"text": row[0], "label": row[1]})
    finally:
        cursor.close()
        conn.close()


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export phpBB3 topic to CSV")
    parser.add_argument("--host", type=str, help="MariaDB host", default="127.0.0.1")
    parser.add_argument("--port", type=int, help="MariaDB port", default=3306)
    parser.add_argument("--user", type=str, help="MariaDB user", default="root")
    parser.add_argument(
        "--database", type=str, help="MariaDB database", default="phpbb3"
    )
    parser.add_argument(
        "--table-prefix", type=str, help="phpBB3 table prefix", default="phpbb_"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--topic-id", type=int, help="phpBB3 topic ID")
    group.add_argument("--forum-id", type=int, help="phpBB3 forum ID")
    parser.add_argument(
        "--output",
        help="Output CSV file",
        type=argparse.FileType("a", encoding="utf-8"),
        default=sys.stdout,
    )
    parser.add_argument(
        "--label",
        type=str,
        choices=LABEL_MAP.keys(),
        help="What label (spam/ham) to assign to posts in this topic",
        required=True,
    )
    return parser.parse_args(args)


def main():
    args = parse_args(sys.argv[1:])
    if os.environ.get("MARIADB_PASSWORD"):
        password = os.environ["MARIADB_PASSWORD"]
    else:
        password = getpass.getpass(
            f"MariaDB password for {args.user} (skip this by setting MARIADB_PASSWORD): "
        )
    if args.topic_id:
        export_phpbb3_topic(
            output=args.output,
            host=args.host,
            port=args.port,
            user=args.user,
            password=password,
            database=args.database,
            table_prefix=args.table_prefix,
            topic_id=args.topic_id,
            label=args.label,
        )
    elif args.forum_id:
        export_phpbb3_forum(
            output=args.output,
            host=args.host,
            port=args.port,
            user=args.user,
            password=password,
            database=args.database,
            table_prefix=args.table_prefix,
            forum_id=args.forum_id,
            label=args.label,
        )
    else:
        raise ValueError("Invalid arguments: either topic_id or forum_id must be set")


if __name__ == "__main__":
    main()
