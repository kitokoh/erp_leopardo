import os
import re

def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def to_camel_case(name):
    return "".join(word.capitalize() for word in name.split('_'))

def parse_sql_type(sql_type):
    sql_type = sql_type.upper()
    if "INTEGER" in sql_type:
        return "Integer"
    if "TEXT" in sql_type:
        return "Text"
    if "REAL" in sql_type:
        return "REAL"
    if "FLOAT" in sql_type:
        return "Float"
    if "BOOL" in sql_type:
        return "Boolean"
    if "DATE" in sql_type:
        return "Date"
    if "TIMESTAMP" in sql_type:
        return "DateTime"
    if "BLOB" in sql_type:
        return "LargeBinary"
    if "NUMERIC" in sql_type:
        return "Numeric"
    return "String"

def parse_create_table(sql):
    table_name_match = re.search(r"CREATE TABLE IF NOT EXISTS `?(\w+)`?", sql, re.IGNORECASE)
    if not table_name_match:
        return None, None
    table_name = table_name_match.group(1)

    columns = []

    # Very basic parsing of columns
    columns_str = re.search(r"\((.*)\)", sql, re.DOTALL).group(1)
    for line in columns_str.split("\n"):
        line = line.strip()
        if not line or line.startswith("FOREIGN KEY") or line.startswith("PRIMARY KEY") or line.startswith("UNIQUE"):
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        col_name = parts[0].strip('`')
        col_type = parse_sql_type(parts[1])

        col_def = {
            "name": col_name,
            "type": col_type,
            "primary_key": "PRIMARY KEY" in line,
            "autoincrement": "AUTOINCREMENT" in line,
            "nullable": "NOT NULL" not in line,
            "unique": "UNIQUE" in line,
            "default": None,
            "foreign_key": None
        }

        fk_match = re.search(r"REFERENCES `?(\w+)`? \(`?(\w+)`?\)", line, re.IGNORECASE)
        if fk_match:
            col_def["foreign_key"] = f"{fk_match.group(1).lower()}.{fk_match.group(2)}"

        columns.append(col_def)

    return table_name, columns

def generate_model_file(table_name, columns, directory):
    class_name = to_camel_case(table_name)
    file_name = to_snake_case(class_name) + ".py"
    filepath = os.path.join(directory, file_name)

    with open(filepath, "w") as f:
        f.write("from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, REAL, Date\n")
        f.write("from sqlalchemy.orm import relationship\n")
        f.write("from sqlalchemy.sql import func\n")
        f.write("from db.connection import Base\n\n")

        f.write(f"class {class_name}(Base):\n")
        f.write(f"    __tablename__ = '{to_snake_case(table_name)}'\n")

        for col in columns:
            col_args = []
            col_args.append(col["type"])

            if col["foreign_key"]:
                col_args.append(f"ForeignKey('{col['foreign_key']}')")

            if col["primary_key"]:
                col_args.append("primary_key=True")
            if col["autoincrement"]:
                col_args.append("autoincrement=True")
            if not col["nullable"]:
                col_args.append("nullable=False")
            if col["unique"]:
                col_args.append("unique=True")

            f.write(f"    {col['name']} = Column({', '.join(col_args)})\n")

        f.write("\n")
        # Basic relationships
        for col in columns:
            if col["foreign_key"]:
                related_table = col["foreign_key"].split('.')[0]
                related_class = to_camel_case(related_table)
                f.write(f"    {related_table[:-1]}_rel = relationship('{related_class}')\n")

        f.write("\n")
        f.write(f"    def __repr__(self):\n")
        f.write(f"        return f'<{class_name} {columns[0]['name']}={{self.{columns[0]['name']}}}>'\n")


def main():
    with open("db/init_schema.py", "r") as f:
        content = f.read()

    # Find all CREATE TABLE statements
    statements = re.findall(r'cursor.execute\s*\(\s*"""(.*?)"""\s*\)', content, re.DOTALL)

    for stmt in statements:
        if "CREATE TABLE" in stmt:
            table_name, columns = parse_create_table(stmt)
            if table_name and columns:
                # Basic grouping logic
                group = "misc"
                if "user" in table_name.lower() or "role" in table_name.lower():
                    group = "users"
                elif "client" in table_name.lower():
                    group = "clients"
                elif "project" in table_name.lower():
                    group = "projects"
                elif "product" in table_name.lower():
                    group = "products"
                elif "order" in table_name.lower() or "commande" in table_name.lower():
                    group = "orders"
                elif "document" in table_name.lower():
                    group = "documents"
                elif "setting" in table_name.lower():
                    group = "settings"
                elif "location" in table_name.lower() or "countr" in table_name.lower() or "cit" in table_name.lower():
                    group = "locations"
                elif "employee" in table_name.lower() or "leave" in table_name.lower():
                    group = "employees"

                dir_path = f"db/models/{group}"
                os.makedirs(dir_path, exist_ok=True)
                generate_model_file(table_name, columns, dir_path)

if __name__ == "__main__":
    main()
