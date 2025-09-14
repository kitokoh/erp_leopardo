import re
import os

def parse_create_table_sql(sql_statement):
    table_name_match = re.search(r'CREATE TABLE IF NOT EXISTS (\w+)', sql_statement, re.IGNORECASE)
    if not table_name_match:
        table_name_match = re.search(r'CREATE TABLE (\w+)', sql_statement, re.IGNORECASE)
    if not table_name_match:
        return None, None

    table_name = table_name_match.group(1)

    columns_str_match = re.search(r'\((.*)\)', sql_statement, re.DOTALL)
    if not columns_str_match:
        return table_name, []

    columns_str = columns_str_match.group(1)

    # Remove everything after the last closing parenthesis of a column definition
    # This is to handle cases where there are table constraints at the end
    last_paren_index = columns_str.rfind(')')
    if last_paren_index != -1:
        # Crude way to check if we are inside a constraint definition
        temp_str = columns_str[:last_paren_index]
        if 'foreign key' in temp_str.lower() or 'primary key' in temp_str.lower() or 'unique' in temp_str.lower():
             pass # This is likely part of a column def with constraint

    lines = columns_str.split('\n')
    columns = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith(('FOREIGN KEY', 'PRIMARY KEY', 'UNIQUE', 'CONSTRAINT')):
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        col_name = parts[0].strip('`"')
        col_type = parts[1].strip(',').upper()

        # Simple type mapping
        sqlalchemy_type = "String"
        if "INT" in col_type:
            sqlalchemy_type = "Integer"
        elif "TEXT" in col_type:
            sqlalchemy_type = "Text"
        elif "REAL" in col_type or "FLOAT" in col_type:
            sqlalchemy_type = "Float"
        elif "BOOL" in col_type:
            sqlalchemy_type = "Boolean"
        elif "DATE" in col_type or "TIME" in col_type:
            sqlalchemy_type = "DateTime"
        elif "NUMERIC" in col_type:
            sqlalchemy_type = "Numeric"
        elif "BLOB" in col_type:
            sqlalchemy_type = "LargeBinary"

        columns.append({'name': col_name, 'type': sqlalchemy_type})

    return table_name, columns

def generate_model_file(table_name, columns):
    class_name = "".join(word.capitalize() for word in table_name.split('_'))
    if not class_name:
        class_name = table_name.capitalize()


    # Convert table name to snake_case for the file name
    file_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower() + ".py"


    # Skip already created files
    if os.path.exists(f"db/models_new/{file_name}"):
        print(f"Skipping {file_name}, already exists.")
        return

    with open(f"db/models_new/{file_name}", 'w') as f:
        f.write("from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Date, Numeric, LargeBinary, ForeignKey\n")
        f.write("from sqlalchemy.orm import relationship\n")
        f.write("from sqlalchemy.sql import func\n")
        f.write("from db.session_manager import Base\n\n")
        f.write(f"class {class_name}(Base):\n")
        f.write(f"    __tablename__ = '{table_name.lower()}'\n\n")

        for col in columns:
            f.write(f"    {col['name']} = Column({col['type']})\n") # Simplified for now

        f.write("\n")
        f.write(f"    def __repr__(self):\n")
        f.write(f"        return f\"<{class_name}>\"\n")

def main():
    with open('db/init_schema.py', 'r') as f:
        content = f.read()

    # Use regex to find all CREATE TABLE statements
    create_table_statements = re.findall(r'cursor.execute\(\s*"""(.*?)"""\s*\)', content, re.DOTALL)

    for stmt in create_table_statements:
        stmt = stmt.strip()
        if stmt.upper().startswith("CREATE TABLE"):
            table_name, columns = parse_create_table_sql(stmt)
            if table_name and columns:
                print(f"Generating model for {table_name}")
                generate_model_file(table_name, columns)

if __name__ == "__main__":
    main()
