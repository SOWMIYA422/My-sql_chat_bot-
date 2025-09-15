import mysql.connector
from textwrap import dedent

# -------------------------------
# 1. Database connection settings
# -------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # change this
    "password": "Yakkay@123",  # change this
    "database": "dares",
}

# -------------------------------
# Root words and synonyms
# -------------------------------
ROOT_WORDS = {
    "id": ["identifier", "number", "code", "key", "ref"],
    "name": ["title", "label", "designation", "description", "fullname"],
    "date": ["day", "time", "datetime", "timestamp", "recorded", "created", "updated"],
    "amount": ["total", "sum", "value", "price", "cost", "charge", "fee"],
    "user": ["customer", "client", "account", "member", "person", "employee"],
    "product": ["item", "goods", "material", "merchandise", "sku"],
    "order": ["purchase", "transaction", "booking", "reservation", "sale"],
    "status": ["state", "condition", "stage", "progress", "flag"],
    "type": ["category", "kind", "class", "group", "variant"],
    "email": ["mail", "contact", "address"],
    "phone": ["contact number", "mobile", "telephone", "cell"],
    "address": ["location", "place", "residence", "street", "city", "postal"],
    "quantity": ["qty", "count", "number of items", "stock", "inventory"],
    "price": ["cost", "rate", "amount", "charge", "fee", "value"],
    "city": ["town", "municipality", "locality"],
    "country": ["nation", "state", "region", "territory"],
    "zip": ["postal code", "postcode", "pincode"],
    "password": ["passcode", "secret", "credential"],
    "active": ["enabled", "working", "live", "operational", "on"],
    "flag": ["marker", "indicator", "signal"],
}


def get_root_words(column_name):
    """Match column names with root words & synonyms."""
    matches = []
    col_lower = column_name.lower()
    for root, synonyms in ROOT_WORDS.items():
        if root in col_lower:
            matches.extend(synonyms + [root])
    return list(set(matches))


# -------------------------------
# 2. Connect to MySQL
# -------------------------------
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# -------------------------------
# 3. Get all tables
# -------------------------------
cursor.execute("SHOW TABLES")
tables = [t[0] for t in cursor.fetchall()]

metadata_text = f"Database Schema: {DB_CONFIG['database']}\n" + "=" * 80 + "\n\n"

# -------------------------------
# 4. Loop over each table
# -------------------------------
for table_name in tables:
    metadata_text += f"Table: {table_name}\n" + "-" * len(f"Table: {table_name}") + "\n"

    # Fetch column info
    cursor.execute(f"SHOW FULL COLUMNS FROM `{table_name}`")
    columns = cursor.fetchall()

    # Fetch foreign keys
    cursor.execute(f"""
        SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = '{DB_CONFIG["database"]}'
          AND TABLE_NAME = '{table_name}'
          AND REFERENCED_TABLE_NAME IS NOT NULL;
    """)
    fk_map = {
        col: (ref_table, ref_col) for col, ref_table, ref_col in cursor.fetchall()
    }

    for col in columns:
        field = col[0]  # Field name
        col_type = col[1]  # Column type
        null = col[3]  # YES/NO for nullable
        key = col[4]  # PRI / MUL / etc.

        nullable = "optional" if null == "YES" else "required"
        pk_text = "Primary Key." if key == "PRI" else ""
        fk_text = ""
        if field in fk_map:
            ref_table, ref_col = fk_map[field]
            fk_text = f"Foreign Key → {ref_table}.{ref_col}."

        # Add root words
        synonyms = get_root_words(field)
        synonyms_text = f" Synonyms: {', '.join(synonyms)}." if synonyms else ""

        metadata_text += (
            f"- {field}: A field of type {col_type} ({nullable}). "
            f"{pk_text} {fk_text}{synonyms_text}\n"
        )

    metadata_text += "\n"

# -------------------------------
# 5. Save to file
# -------------------------------
with open("richmetadata.txt", "w", encoding="utf-8") as f:
    f.write(metadata_text)

cursor.close()
conn.close()
print("✅ richmetadata.txt generated successfully.")
