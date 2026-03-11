import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.duckdb_manager import DuckDBManager
from data.schema_definitions import (schema)

db=DuckDBManager()

result=db.execute_query("""select * from service_provider_billing limit 10""")

print(result)
