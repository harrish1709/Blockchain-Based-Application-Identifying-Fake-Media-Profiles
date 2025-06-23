import sqlite3

# Establish a connection to the SQLite database
conn = sqlite3.connect('users.db')

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Execute the SQL query to create the users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
''')

# Commit the changes and close the connection
conn.commit()
conn.close()

print('SQLite database file "users.db" created successfully with the "users" table.')
