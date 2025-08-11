import os
import re

def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def to_camel_case(name):
    return "".join(word.capitalize() for word in name.split('_'))

def add_foreign_keys_to_model(filepath, foreign_keys):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped_line = line.strip()

        # Check if this line defines a column that should be a foreign key
        for fk in foreign_keys:
            if stripped_line.startswith(fk['column']):
                # This is the line to modify
                # Very basic replacement, might not work for all cases
                line = line.replace(")", f", ForeignKey('{fk['references']}'))\n")
                break
        new_lines.append(line)

    # Add relationships at the end of the class
    for fk in foreign_keys:
        related_table = fk['references'].split('.')[0]
        related_class = to_camel_case(related_table)
        new_lines.append(f"    {related_table[:-1]}_rel = relationship('{related_class}')\n")

    with open(filepath, 'w') as f:
        f.writelines(new_lines)

def parse_foreign_keys_from_sql(sql):
    foreign_keys = []
    # Find all FOREIGN KEY constraints
    fk_matches = re.findall(r"FOREIGN KEY \(`?(\w+)`?\) REFERENCES `?(\w+)`? \(`?(\w+)`?\)", sql, re.IGNORECASE)
    for match in fk_matches:
        foreign_keys.append({
            "column": match[0],
            "references": f"{match[1].lower()}.{match[2]}"
        })
    return foreign_keys

def main():
    with open("db/init_schema.py", "r") as f:
        content = f.read()

    # Find all CREATE TABLE statements
    statements = re.findall(r'cursor.execute\s*\(\s*"""(.*?)"""\s*\)', content, re.DOTALL)

    for stmt in statements:
        if "CREATE TABLE" in stmt:
            table_name_match = re.search(r"CREATE TABLE IF NOT EXISTS `?(\w+)`?", stmt, re.IGNORECASE)
            if not table_name_match:
                continue
            table_name = table_name_match.group(1)

            foreign_keys = parse_foreign_keys_from_sql(stmt)
            if not foreign_keys:
                continue

            # Find the corresponding model file
            class_name = to_camel_case(table_name)
            file_name = to_snake_case(class_name) + ".py"

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

            filepath = f"db/models/{group}/{file_name}"
            if os.path.exists(filepath):
                print(f"Processing {filepath}")
                add_foreign_keys_to_model(filepath, foreign_keys)

if __name__ == "__main__":
    main()
