import re

def comment_out_schema_creation(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    in_multiline_execute = False
    for line in lines:
        stripped_line = line.strip()

        # Check for start of multiline execute block
        if stripped_line.startswith('cursor.execute("""'):
            # Check if it's a CREATE statement
            if "CREATE TABLE" in stripped_line.upper() or \
               "CREATE INDEX" in stripped_line.upper() or \
               "ALTER TABLE" in stripped_line.upper():
                in_multiline_execute = True

        if in_multiline_execute:
            new_lines.append("#" + line)
        else:
            new_lines.append(line)

        # Check for end of multiline execute block
        if stripped_line.endswith('""")') and in_multiline_execute:
            in_multiline_execute = False

    with open(filepath, 'w') as f:
        f.writelines(new_lines)

def main():
    filepath = 'db/init_schema.py'
    print(f"Commenting out schema creation in {filepath}")
    comment_out_schema_creation(filepath)
    print("Done.")

if __name__ == "__main__":
    main()
