import os
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def find_missing_foreign_keys():
    models_dir = 'db/models'
    log_file = 'missing_foreign_keys.log'

    relationship_pattern = re.compile(r'(\w+)\s*=\s*relationship\("(\w+)"')
    foreign_key_pattern = re.compile(r'ForeignKey\s*\(\s*[\'"](\w+)\..*[\'"]\s*\)')

    with open(log_file, 'w') as f:
        for subdir, _, files in os.walk(models_dir):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(subdir, file)
                    with open(filepath, 'r', encoding='utf-8') as model_file:
                        content = model_file.read()
                        relationships = relationship_pattern.findall(content)
                        foreign_keys = foreign_key_pattern.findall(content)

                        if not relationships:
                            continue

                        f.write(f"--- Checking {filepath} ---\n")

                        for rel_name, rel_class in relationships:
                            # This is a heuristic. A relationship to 'User' needs a 'user_id' foreign key.
                            # The target table is usually plural, e.g., relationship("User") -> table 'users'
                            # The foreign key is usually 'users.id' or 'users.user_id'
                            # This is not perfect, but it's a good start.

                            # A simple check: if a relationship exists, there must be at least one foreign key in the file.
                            # This is a weak check, but it's a start.
                            if not foreign_keys:
                                f.write(f"  [POTENTIAL ISSUE] File has relationships but NO ForeignKeys. Relationship: {rel_name} -> {rel_class}\n")
                                continue

    logging.info(f"Finished checking for missing foreign keys. Results are in {log_file}")

if __name__ == "__main__":
    find_missing_foreign_keys()
