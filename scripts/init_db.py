import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.duckdb_manager import DuckDBManager
from data.schema_definitions import (schema)

def init_database():
    db=DuckDBManager()
    for table_name in schema.keys():
        db.create_table(schema[table_name])
        print(db.insert_data(table_name,f'data/raw/{table_name}.csv'))
    
    db.close()

if __name__ == "__main__":
    init_database()
