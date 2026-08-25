import duckdb
conn = duckdb.connect("data/processed/tps_komersial.duckdb", read_only=True)
query = """
    SELECT table_name, column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema='main' and table_name='fakta_market_share'
    ORDER BY table_name, ordinal_position;
"""
print(conn.execute(query).df())
conn.close()
