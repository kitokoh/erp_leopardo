import os
import re

def add_table_args_to_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Check if __table_args__ is already present
    if '__table_args__' in content:
        return

    # Add __table_args__ before the __repr__ method
    new_content = re.sub(r"(\s*def __repr__)", r"\n    __table_args__ = {'extend_existing': True}\1", content)

    with open(filepath, 'w') as f:
        f.write(new_content)

def main():
    models_dir = 'db/models'
    for subdir, _, files in os.walk(models_dir):
        for filename in files:
            if filename.endswith('.py') and filename != '__init__.py':
                filepath = os.path.join(subdir, filename)
                print(f"Processing {filepath}")
                add_table_args_to_file(filepath)

if __name__ == "__main__":
    main()
