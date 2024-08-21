import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('library.db')
c = conn.cursor()

# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS Books (
    book_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    published_year INTEGER NOT NULL,
    image_url TEXT,
    available BOOLEAN NOT NULL CHECK (available IN (0, 1))
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS Members (
    member_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
)
''')

c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

c.execute('''
CREATE TABLE IF NOT EXISTS Loans (
    loan_id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL,
    member_id INTEGER NOT NULL,
    loan_date TEXT NOT NULL,
    return_date TEXT,
    due_date TEXT,
    FOREIGN KEY (book_id) REFERENCES Books(book_id),
    FOREIGN KEY (member_id) REFERENCES Members(member_id)
)
''')

# Insert some realistic data
books = [
    ('Harry Potter and the Philosopher\'s Stone', 'J.K. Rowling', 1997, 1),
    ('The Great Gatsby', 'F. Scott Fitzgerald', 1925, 1),
    ('To Kill a Mockingbird', 'Harper Lee', 1960, 1)
]

members = [
    ('John Doe'),
    ('Jane Smith')
]

for book in books:
    c.execute('INSERT INTO Books (title, author, published_year, available) VALUES (?, ?, ?, ?)', book)

for member in members:
    c.execute('INSERT INTO Members (name) VALUES (?)', (member,))

users = [
    ('admin', 'admin123'),
    ('user1', 'password1'),
    ('user2', 'password2')
]

for user in users:
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', user)


conn.commit()
conn.close()

import sqlite3

conn = sqlite3.connect('library.db')
c = conn.cursor()


from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def hash_existing_passwords():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()

    # Retrieve all users
    users = c.execute('SELECT id, password FROM users').fetchall()

    # Hash each password and update the database
    for user in users:
        user_id = user[0]
        plain_text_password = user[1]
        hashed_password = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
        c.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))

    conn.commit()
    conn.close()

hash_existing_passwords()
