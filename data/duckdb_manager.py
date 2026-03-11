import duckdb
from typing import Optional
import os
from decimal import Decimal
import uuid
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DuckDBManager:
    def __init__(self,DBName:str='data/warehouse.duckdb'):
        self.conn=None 
        self.DBName=DBName
        self._initialise_DB()
    
    def _initialise_DB(self):
        """Create DuckDB connection."""
        self.conn=duckdb.connect(self.DBName)
    
    def _table_data(self,table_name:str)->bool:
        exists=self.conn.execute(f"select exists(select 1 from information_schema.tables where table_name='{table_name}')").fetchone()[0]

        if exists:
            count=self.conn.execute(f"select count(*) from {table_name}").fetchone()[0]

            return False if count<=0 else True

        return False

    def execute_query(self,query)->list[dict]:
        rows = self.conn.execute(query).fetchall()
        cols = [desc[0] for desc in self.conn.description] # stores information about the result set schema
        results=[]

        for row in rows:
            clean_row={}
            for col, val in zip(cols, row):
                # Convert Decimal to float so json.dumps works cleanly
                clean_row[col] = float(val) if isinstance(val, Decimal) else val
            results.append(clean_row)
        return results

    def get_table_schema(self, table_name: str):
        """
        Returns column metadata for a table.
        """
        query = """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = ?
            ORDER BY ordinal_position
        """

        result = self.conn.execute(query, [table_name]).fetchall()

        return [
            {"column": row[0], "type": row[1]}
            for row in result
        ]

    def create_table(self,schema:str):
        self.conn.execute(schema)
        print('table created successfully!!')
        print(schema)
    
    def insert_data(self,tableName:str,filePath:str):
        file_data=self.conn.read_csv(filePath,header=True,sep=',')

        if not self._table_data(tableName):
            self.conn.execute(f"INSERT INTO {tableName} SELECT * FROM file_data")  

        return self.conn.execute(f"SELECT count(*) FROM {tableName}").fetchall()

    def _ensure_feedback_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS query_feedback (
            id          VARCHAR PRIMARY KEY,
            question    TEXT,
            sql         TEXT,
            answer      TEXT,
            rating      INTEGER,   -- 1=thumbsup, 0=thumbsdown
            created_at  TIMESTAMP DEFAULT current_timestamp
        )
    """)

    def save_feedback(self, question, sql, answer, rating):
        self._ensure_feedback_table()
        self.conn.execute("""
            INSERT INTO query_feedback (id, question, sql, answer, rating)
            VALUES (?, ?, ?, ?, ?)
        """, [str(uuid.uuid4()),question, sql, answer, rating])

    def close(self):
        if self.conn:
            self.conn.close()

    

