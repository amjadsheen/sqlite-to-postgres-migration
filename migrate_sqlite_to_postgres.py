#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
This script exports data from SQLite and imports it into PostgreSQL
"""

import sqlite3
import psycopg2
import sys
import json
from datetime import datetime

# PostgreSQL connection configuration
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'dbname',
    'user': 'dbname_user',
    'password': '1234'
}

def get_sqlite_tables(cursor):
    """Get all table names from SQLite database"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return [row[0] for row in cursor.fetchall()]

def get_table_schema(cursor, table_name):
    """Get table schema from SQLite"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()

def sqlite_type_to_postgres(sqlite_type):
    """Convert SQLite data types to PostgreSQL data types"""
    type_mapping = {
        'INTEGER': 'INTEGER',
        'TEXT': 'TEXT',
        'REAL': 'REAL',
        'BLOB': 'BYTEA',
        'NUMERIC': 'NUMERIC',
        'VARCHAR': 'VARCHAR',
        'DATETIME': 'TIMESTAMP',
        'DATE': 'DATE',
        'TIME': 'TIME',
        'BOOLEAN': 'BOOLEAN',
        'JSON': 'JSONB'
    }
    
    sqlite_type_upper = sqlite_type.upper()
    for key in type_mapping:
        if key in sqlite_type_upper:
            return type_mapping[key]
    return 'TEXT'  # Default fallback

def create_postgres_table(pg_cursor, table_name, schema):
    """Create table in PostgreSQL based on SQLite schema"""
    columns = []
    for col in schema:
        col_id, col_name, col_type, not_null, default_val, pk = col
        pg_type = sqlite_type_to_postgres(col_type)
        
        column_def = f'"{col_name}" {pg_type}'
        
        if pk:
            column_def += ' PRIMARY KEY'
        elif not_null:
            column_def += ' NOT NULL'
            
        if default_val is not None and not pk:
            column_def += f" DEFAULT {default_val}"
            
        columns.append(column_def)
    
    create_table_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(columns)});'
    
    try:
        pg_cursor.execute(create_table_sql)
        print(f"✓ Created table: {table_name}")
    except Exception as e:
        print(f"✗ Error creating table {table_name}: {e}")
        raise

def get_postgres_column_types(pg_cursor, table_name):
    """Get PostgreSQL column types for a table"""
    pg_cursor.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
    """)
    return {row[0]: row[1] for row in pg_cursor.fetchall()}

def convert_value(value, pg_type):
    """Convert SQLite value to PostgreSQL-compatible value"""
    if value is None:
        return None
    
    # Handle boolean conversions (SQLite stores as INTEGER 0/1)
    if pg_type == 'boolean':
        if isinstance(value, (int, float)):
            return bool(value)
        elif isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 't')
        return bool(value)
    
    # Handle timestamp conversions (SQLite stores as INTEGER milliseconds)
    elif pg_type in ('timestamp without time zone', 'timestamp with time zone'):
        if isinstance(value, (int, float)):
            # Convert milliseconds to seconds and create timestamp
            try:
                return datetime.fromtimestamp(value / 1000.0)
            except:
                return value
    
    # Handle date conversions
    elif pg_type == 'date':
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value / 1000.0).date()
            except:
                return value
    
    # Handle time conversions
    elif pg_type == 'time without time zone':
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value / 1000.0).time()
            except:
                return value
    
    return value

def migrate_table_data(sqlite_cursor, pg_cursor, table_name):
    """Copy data from SQLite table to PostgreSQL table"""
    # Get all data from SQLite
    sqlite_cursor.execute(f'SELECT * FROM "{table_name}"')
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"  ⚠ Table {table_name} is empty")
        return
    
    # Get column names and types
    column_names = [description[0] for description in sqlite_cursor.description]
    pg_types = get_postgres_column_types(pg_cursor, table_name)
    
    placeholders = ', '.join(['%s'] * len(column_names))
    columns_str = ', '.join([f'"{col}"' for col in column_names])
    
    insert_sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'
    
    try:
        # Convert and insert data in batches
        batch_size = 100
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            
            # Convert values based on PostgreSQL column types
            converted_batch = []
            for row in batch:
                converted_row = []
                for col_name, value in zip(column_names, row):
                    pg_type = pg_types.get(col_name, 'text')
                    converted_value = convert_value(value, pg_type)
                    converted_row.append(converted_value)
                converted_batch.append(tuple(converted_row))
            
            pg_cursor.executemany(insert_sql, converted_batch)
        
        print(f"✓ Migrated {len(rows)} rows to {table_name}")
    except Exception as e:
        print(f"✗ Error migrating data to {table_name}: {e}")
        raise

def main():
    sqlite_db_path = 'data.db'
    
    print("=" * 60)
    print("SQLite to PostgreSQL Migration Script")
    print("=" * 60)
    print()
    
    # Update PostgreSQL configuration
    print("PostgreSQL Configuration:")
    print(f"  Host: {PG_CONFIG['host']}")
    print(f"  Port: {PG_CONFIG['port']}")
    print(f"  Database: {PG_CONFIG['database']}")
    print(f"  User: {PG_CONFIG['user']}")
    print()
    
    response = input("Continue with migration? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Migration cancelled.")
        return
    
    try:
        # Connect to SQLite
        print("\n📦 Connecting to SQLite database...")
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Connect to PostgreSQL
        print("🐘 Connecting to PostgreSQL database...")
        pg_conn = psycopg2.connect(**PG_CONFIG)
        pg_cursor = pg_conn.cursor()
        
        # Get all tables from SQLite
        tables = get_sqlite_tables(sqlite_cursor)
        print(f"\n📋 Found {len(tables)} tables to migrate")
        print()
        
        # Migrate each table
        for table in tables:
            print(f"Processing table: {table}")
            
            # Get schema
            schema = get_table_schema(sqlite_cursor, table)
            
            # Create table in PostgreSQL
            create_postgres_table(pg_cursor, table, schema)
            
            # Migrate data
            migrate_table_data(sqlite_cursor, pg_cursor, table)
            
            print()
        
        # Commit changes
        pg_conn.commit()
        
        print("=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        
    except sqlite3.Error as e:
        print(f"\n✗ SQLite error: {e}")
        sys.exit(1)
    except psycopg2.Error as e:
        print(f"\n✗ PostgreSQL error: {e}")
        if pg_conn:
            pg_conn.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        if pg_conn:
            pg_conn.rollback()
        sys.exit(1)
    finally:
        # Close connections
        if sqlite_cursor:
            sqlite_cursor.close()
        if sqlite_conn:
            sqlite_conn.close()
        if pg_cursor:
            pg_cursor.close()
        if pg_conn:
            pg_conn.close()

if __name__ == '__main__':
    main()
