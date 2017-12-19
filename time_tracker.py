"""Simple command-line interface for tracking time spent on tasks."""

import dateutil.parser
import os
import sqlite3

from datetime import datetime
from uuid import uuid4


def main():
    """Execute the core program functionality."""
    database_path = os.environ.get('TIMETRACKER_DBPATH')
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    cur.execute("""
        create table if not exists sessions (
            id text not null primary key,
            session_start text not null,
            session_end text);
        """)
    cur.execute("""
        create table if not exists tasks (
            id text not null primary key,
            session_id text not null,
            task_start text not null,
            task_end text,
            duration real,
            task_text text,
            foreign key(session_id) references sessions(id));
        """)
    conn.commit()
    session_id = uuid4().hex
    timestamp_now = datetime.now().isoformat()

    cur.execute("""
        insert into sessions (id, session_start) values (
            ?, ?);
        """, (session_id, timestamp_now))
    conn.commit()

    session_complete = False

    last_task_id = None

    while not session_complete:
        task_text = input('> ')
        current_time = datetime.now()
        current_time_string = current_time.isoformat()
        task_id = uuid4().hex

        if last_task_id:
            last_task_end = current_time
            cur.execute("""update tasks
                set task_end = ?
                where id = ?;
                """, (last_task_end, last_task_id))
            cur.execute("""select
                task_start from tasks
                where id = ?;
                """, (last_task_id,))
            last_task_start = dateutil.parser.parse(cur.fetchone()[0])
            duration = (last_task_end - last_task_start).seconds
            cur.execute("""update tasks
                set duration = ?
                where id = ?;
                """, (duration, last_task_id))
            conn.commit()

        if task_text == 'done':
            cur.execute("""
                update sessions
                set session_end = ?
                where id = ?;
                """, (current_time_string, session_id))
            conn.commit()
            session_complete = True
        else:
            cur.execute("""
                insert into tasks (id, session_id, task_start, task_text)
                values (
                    ?, ?, ?, ?);
                """, (task_id, session_id, current_time_string, task_text))
            conn.commit()
        last_task_id = task_id

    conn.close()
    print('Session ended.')


if __name__ == '__main__':
    main()
