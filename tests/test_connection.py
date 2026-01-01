#!/usr/bin/env python3
"""
Test Oracle connection
"""
import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

# Database configuration
host = os.getenv('ORACLE_HOST')
port = int(os.getenv('ORACLE_PORT', 1521))
service_name = os.getenv('ORACLE_SERVICE_NAME')
username = os.getenv('ORACLE_USERNAME')
password = os.getenv('ORACLE_PASSWORD')

print(f"Host: {host}")
print(f"Port: {port}")
print(f"Service: {service_name}")
print(f"Username: {username}")

# Try different connection formats
dsn_formats = [
    f"{host}:{port}/{service_name}",
    f"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={host})(PORT={port}))(CONNECT_DATA=(SERVICE_NAME={service_name})))",
    f"//{host}:{port}/{service_name}"
]

for i, dsn in enumerate(dsn_formats):
    print(f"\nTrying DSN format {i+1}: {dsn}")
    try:
        connection = oracledb.connect(
            user=username,
            password=password,
            dsn=dsn
        )
        print("✅ Connection successful!")
        connection.close()
        break
    except Exception as e:
        print(f"❌ Failed: {e}")