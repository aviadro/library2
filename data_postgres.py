import os
import psycopg2
from psycopg2 import sql

# Connect to PostgreSQL database
conn = psycopg2.connect(
    dbname="library_vjk0",
    user="library_vjk0_user",
    password=os.getenv('PASSWORD'),
    host="dpg-cr6925jtq21c73bbihtg-a.oregon-postgres.render.com",
    port="5432"
)
c = conn.cursor()

# Create tables
c.execute('''
CREATE TABLE IF NOT EXISTS Books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    published_year INTEGER NOT NULL,
    image_url TEXT,
    available BOOLEAN NOT NULL CHECK (available IN (TRUE, FALSE))
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS Members (
    member_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password TEXT NOT NULL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS Loans (
    loan_id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES Books(book_id),
    member_id INTEGER NOT NULL REFERENCES Members(member_id),
    loan_date DATE NOT NULL,
    return_date DATE,
    due_date DATE
)
''')


# Insert some realistic data
books = [
    ('Harry Potter and the Philosopher\'s Stone', 'J.K. Rowling', 1997,"https://m.media-amazon.com/images/I/81DI+BAN2SL._AC_UF1000,1000_QL80_.jpg", True),
    ('The Great Gatsby', 'F. Scott Fitzgerald', 1925,"https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSKi5lknrw7SIwZ01RQRqyvtXz2bFxrUsGVpA&s", True),
    ('To Kill a Mockingbird', 'Harper Lee', 1960, None, True),
    ("הכוזרי","ר יהודה הלוי",1139,"https://www.derechaimss.co.il/wp-content/uploads/2023/03/544456.webp",True),
    ("1984","George Orwell",1949,"https://www.booknet.co.il/Images/Site/Products/9780141036144.jpg",True),
    ("Pride and Prejudice","Jane Austen",1813,"https://www.wizkids.co.il/cdn/shop/products/PrideandPrejudice_x700.jpg?v=1655391423",True),
    ("The Catcher in the Rye","J.D. Salinger",1951, None, True)
]

members = [
    ('John Doe',),
    ('Jane Smith',),
    ('yisraela',),
    ('Aviad Roichman',)
]

for book in books:
    c.execute('INSERT INTO Books (title, author, published_year, image_url, available) VALUES (%s, %s, %s, %s, %s)', book)

for member in members:
    c.execute('INSERT INTO Members (name) VALUES (%s)', member)

users = [
    ('admin', 'admin123'),
    ('user1', 'password1'),
    ('user2', 'password2')
]

for user in users:
    c.execute('INSERT INTO users (username, password) VALUES (%s, %s)', user)

conn.commit()
conn.close()

# Reconnect to hash passwords
import psycopg2
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def hash_existing_passwords():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    c = conn.cursor()

    # Retrieve all users
    c.execute('SELECT id, password FROM users')  # Execute the query
    users = c.fetchall()  # Fetch all results

    # Hash each password and update the database
    for user in users:
        user_id = user[0]
        plain_text_password = user[1]
        hashed_password = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
        c.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, user_id))

    conn.commit()
    conn.close()

hash_existing_passwords()

