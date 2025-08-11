import os
import re

def fix_tablename_in_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find the class name
    class_name_match = re.search(r'class\s+(\w+)\(Base\):', content)
    if not class_name_match:
        return

    class_name = class_name_match.group(1)

    # Convert class name to snake_case for the tablename
    snake_case_table_name = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()

    # Replace the existing __tablename__
    new_content = re.sub(r"__tablename__ = '.*'", f"__tablename__ = '{snake_case_table_name}'", content)

    with open(filepath, 'w') as f:
        f.write(new_content)

def main():
    models_dir = 'db/models_new'
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            print(f"Processing {filepath}")
            fix_tablename_in_file(filepath)

if __name__ == "__main__":
    main()
