"""
Common utilities for the USPTO Patents Processing Python project

This module provides common utilities for the USPTO Patents Processing Python project. It includes functions to load configuration files, load application keys, and load modules dynamically.

Todos:
- Add more functions for common utilities.
- Add more error handling and logging.
- Add more documentation.
- Add monitoring and alerting
"""
import asyncpg
import psycopg2

class PostgresHelpers:
    @staticmethod
    def connect_psycopg2(pgsql_params):
        conn_params = pgsql_params.copy()
        conn_params.pop('database', None)  # Remove 'database' key if it exists
        conn = psycopg2.connect(**conn_params)
        return conn

    @staticmethod
    async def connect_asyncpg(pgsql_params):
        conn_params = pgsql_params.copy()
        conn_params.pop('dbname', None)  # Remove 'dbname' key if it exists
        conn = await asyncpg.connect(**conn_params)
        return conn