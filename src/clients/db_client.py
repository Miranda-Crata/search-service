import os
import psycopg2
from psycopg2.extras import RealDictCursor

_connection = None


def get_connection():
    global _connection
    if _connection is None or _connection.closed:
        _connection = psycopg2.connect(
            dsn=os.environ["SUPABASE_DB_URL"],
            cursor_factory=RealDictCursor,
        )
        _connection.autocommit = True
    return _connection
