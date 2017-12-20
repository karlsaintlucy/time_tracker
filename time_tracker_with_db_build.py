"""Command-line interface for tracking time spent."""

import bcrypt
import dateutil.parser
import getpass
import os
import sqlite3

from datetime import datetime
from uuid import uuid4


def main():
    """Execute the core program functionality."""
    # database_path = os.environ.get('TIMETRACKER_DBPATH')
    database_path = 'time_tracker.db'
    conn = sqlite3.connect(database_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT NOT NULL PRIMARY KEY,
            session_start TEXT NOT NULL,
            session_end TEXT);
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT NOT NULL PRIMARY KEY,
            task_start TEXT NOT NULL,
            task_end TEXT,
            duration_in_minutes INTEGER,
            description TEXT);
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions_tasks (
            session_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(id),
            FOREIGN KEY(task_id) REFERENCES tasks(id),
            PRIMARY KEY(session_id, task_id)
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS depts (
            id TEXT NOT NULL PRIMARY KEY,
            long_name TEXT NOT NULL UNIQUE,
            short_name TEXT NOT NULL UNIQUE,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            employee_count INTEGER);
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id TEXT NOT NULL PRIMARY KEY,
            street_address_1 TEXT,
            street_address_2 TEXT,
            city TEXT NOT NULL,
            state_fullname TEXT,
            state_shortcode TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            country TEXT);
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT NOT NULL PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT username_email_unique UNIQUE (username, email));
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payrates (
            id TEXT NOT NULL PRIMARY KEY,
            hourly_rate REAL NOT NULL,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_depts (
            user_id TEXT NOT NULL,
            dept_id TEXT NOT NULL,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(dept_id) REFERENCES depts(id),
            PRIMARY KEY(user_id, dept_id));

        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_locations (
            user_id TEXT NOT NULL,
            location_id TEXT NOT NULL,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(location_id) REFERENCES locations(id),
            PRIMARY KEY(user_id, location_id));
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_sessions (
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(session_id) REFERENCES sessions(id),
            PRIMARY KEY(user_id, session_id));
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_payrates (
            user_id TEXT NOT NULL,
            payrate_id TEXT NOT NULL,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(payrate_id) REFERENCES payrates(id),
            PRIMARY KEY(user_id, payrate_id));
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_roles (
            user_id TEXT NOT NULL,
            role_id TEXT NOT NULL,
            created TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(role_id) REFERENCES roles(id),
            PRIMARY KEY(user_id, role_id));
        """)
    conn.commit()

    session_id = login(conn, cur)
    timestamp_now = datetime.now().isoformat()

    cur.execute("""
        INSERT INTO sessions (id, session_start) VALUES (
            ?, ?);
        """, (session_id, timestamp_now))
    conn.commit()

    session_complete = False

    last_task_id = None

    while not session_complete:
        os.system('cls' if os.name == 'nt' else 'clear')
        print('{:.^79s}'.format('Time Tracker 0.0'))
        task_text = input('$$ ')
        current_time = datetime.now()
        current_time_string = current_time.isoformat()
        task_id = uuid4().hex

        if last_task_id:
            last_task_end = current_time
            cur.execute("""UPDATE tasks
                SET task_end = ?
                WHERE id = ?;
                """, (last_task_end, last_task_id))
            cur.execute("""SELECT
                task_start FROM tasks
                WHERE id = ?;
                """, (last_task_id,))
            last_task_start = dateutil.parser.parse(cur.fetchone()[0])
            duration = (last_task_end - last_task_start).seconds
            cur.execute("""UPDATE tasks
                SET duration = ?
                WHERE id = ?;
                """, (duration, last_task_id))
            conn.commit()

        if task_text == 'end session':
            cur.execute("""
                UPDATE sessions
                SET session_end = ?
                WHERE id = ?;
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


def create_user():
    user = getpass.getpass(prompt='User: ')
    password = getpass.getpass(prompt='Password: ')
    password_bytes = password.encode()
    password_hashed = bcrypt.hashpw(
        session_password_bytes, bcrypt.gensalt())


def login(conn, cur):
    session_user = input('User: ')
    session_password = getpass.getpass(prompt='Password: ')
    cur.execute("""
        select password from users where user_name = ?;
        """, (session_user,))
    hashed = cur.fetchone()[0]
    conn.commit()
    if bcrypt.hashpw(session_password, hashed) == hashed:
        session_id = uuid4().hex
        return session_id

if __name__ == '__main__':
    main()
