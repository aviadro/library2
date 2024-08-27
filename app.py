from flask import Flask, flash, request, jsonify, render_template, redirect, session, url_for
import sqlite3
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os
from psycopg2.extras import DictCursor  # ייבוא מפורש של DictCursor


import psycopg2

# טוען את משתני הסביבה מהקובץ .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)


def get_db_connection():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )
    return conn

# Endpoint to show list of books and their status
@app.route('/')
def show_books():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM Books')
    books = c.fetchall()
    conn.close()
    return render_template('show_books.html', books=books)

@app.route('/show_members')
def show_members():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get all members
    c.execute('SELECT * FROM Members')
    members = c.fetchall()
    
    # Get all books that are currently on loan and not returned yet, including loan date
    c.execute('''
    SELECT Members.member_id, Members.name, Books.title, Loans.loan_date, Loans.due_date
    FROM Members
    LEFT JOIN Loans ON Members.member_id = Loans.member_id
    LEFT JOIN Books ON Loans.book_id = Books.book_id
    WHERE Loans.return_date IS NULL
    ORDER BY Members.member_id
    ''')
    member_loans = c.fetchall()
    
    conn.close()
    
    return render_template('show_members.html', members=members, member_loans=member_loans)




# Endpoint to add a book
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        book_details = request.form
        title = book_details['title']
        author = book_details['author']
        published_year = book_details['published_year']
        image_url = book_details.get('image_url', '')  # Get the image URL

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO Books (title, author, published_year, available, image_url) VALUES (%s, %s, %s, TRUE, %s)', 
                  (title, author, published_year, image_url))
        conn.commit()
        conn.close()

        return redirect(url_for('show_books'))
    return render_template('add_book.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        conn.row_factory = DictCursor  # שימוש ב-DictCursor לייצוג השורות כמילון
        user = conn.cursor().execute('SELECT * FROM users WHERE username = %s', (username,)).fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('show_books'))
        else:
            return "Invalid username or password."
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('show_books'))

# Endpoint to add a member
@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        member_details = request.form
        name = member_details['name']
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO Members (name) VALUES (%s)', (name,))
        conn.commit()
        conn.close()
        
        return redirect(url_for('show_books'))
    return render_template('add_member.html')

# Endpoint to loan a book
@app.route('/loan_book', methods=['GET', 'POST'])
def loan_book():
    if request.method == 'POST':
        loan_details = request.form
        book_id = loan_details['book_id']
        member_id = loan_details['member_id']
        loan_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        due_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE Books SET available = FALSE WHERE book_id = %s', (book_id,))
        c.execute('INSERT INTO Loans (book_id, member_id, loan_date, due_date) VALUES (%s, %s, %s, %s)', 
                  (book_id, member_id, loan_date, due_date))
        conn.commit()
        conn.close()
        
        return redirect(url_for('show_books'))
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM Books WHERE available = TRUE')
    books = c.fetchall()
    c.execute('SELECT * FROM Members')
    members = c.fetchall()
    conn.close()
    return render_template('loan_book.html', books=books, members=members)



# Endpoint to return a book
@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        return_details = request.form
        loan_id = return_details['loan_id']
        return_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT due_date FROM Loans WHERE loan_id = %s', (loan_id,))
        due_date = c.fetchone()[0]
        
        if datetime.strptime(return_date, '%Y-%m-%d %H:%M:%S') > datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S'):
            # Book is returned late - you can add code to handle such cases
            flash("The book was returned late", 'danger')

        c.execute('UPDATE Loans SET return_date = %s WHERE loan_id = %s', (return_date, loan_id))
        c.execute('UPDATE Books SET available = TRUE WHERE book_id = (SELECT book_id FROM Loans WHERE loan_id = %s)', (loan_id,))
        conn.commit()
        conn.close()
        
        return redirect(url_for('show_books'))
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
    SELECT Loans.loan_id, Books.title, Books.author, Members.name
    FROM Loans
    JOIN Books ON Loans.book_id = Books.book_id
    JOIN Members ON Loans.member_id = Members.member_id
    WHERE Loans.return_date IS NULL
    ''')
    loans = c.fetchall()

    conn.close()
    return render_template('return_book.html', loans=loans)

@app.route('/update_book/<int:book_id>', methods=['GET', 'POST'])
def update_book(book_id):
    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        updated_details = request.form
        title = updated_details['title']
        author = updated_details['author']
        published_year = updated_details['published_year']
        image_url = updated_details.get('image_url', '')

        c.execute('''
            UPDATE Books
            SET title = %s, author = %s, published_year = %s, image_url = %s
            WHERE book_id = %s
        ''', (title, author, published_year, image_url, book_id))
        conn.commit()
        conn.close()

        return redirect(url_for('show_books'))

    c.execute('SELECT * FROM Books WHERE book_id = %s', (book_id,))
    book = c.fetchone()
    conn.close()

    return render_template('update_book.html', book=book)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user_id' not in session:
        flash('To delete, you need to login first.', "danger")
        return redirect(url_for('show_books'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM Books WHERE book_id = %s', (book_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('show_books'))

@app.route('/update_member/<int:member_id>', methods=['GET', 'POST'])
def update_member(member_id):
    conn = get_db_connection()
    c = conn.cursor()

    if request.method == 'POST':
        updated_details = request.form
        name = updated_details['name']
        c.execute('UPDATE Members SET name = %s WHERE member_id = %s', (name, member_id))
        conn.commit()
        conn.close()
        return redirect(url_for('show_members'))

    c.execute('SELECT * FROM Members WHERE member_id = %s', (member_id,))
    member = c.fetchone()
    conn.close()

    return render_template('update_member.html', member=member)


@app.route('/delete_member/<int:member_id>', methods=['POST'])
def delete_member(member_id):
    if 'user_id' not in session:
        flash('To delete member, you need to login first.', "danger")
        return redirect(url_for('show_members'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM Members WHERE member_id = %s', (member_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('show_members'))

@app.route('/search_books', methods=['GET', 'POST'])
def search_books():
    query = ''
    books = []
    
    if request.method == 'POST':
        query = request.form['query']
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT * FROM Books
            WHERE title LIKE %s OR author LIKE %s
        ''', ('%' + query + '%', '%' + query + '%'))
        books = c.fetchall()
        conn.close()
    
    return render_template('search_books.html', query=query, books=books)

@app.route('/statistics')
def statistics():
    conn = get_db_connection()
    c = conn.cursor()

    # Get the total number of books
    c.execute('SELECT COUNT(*) FROM Books')
    total_books = c.fetchone()[0]

    # Get the number of currently loaned books
    c.execute('SELECT COUNT(*) FROM Loans WHERE return_date IS NULL')
    loaned_books = c.fetchone()[0]

    # Get the total number of members
    c.execute('SELECT COUNT(*) FROM Members')
    total_members = c.fetchone()[0]

    # Get the number of books available
    c.execute('SELECT COUNT(*) FROM Books WHERE available = TRUE')
    available_books = c.fetchone()[0]

    conn.close()

    return render_template('statistics.html', total_books=total_books, loaned_books=loaned_books, total_members=total_members, available_books=available_books)



if __name__ == '__main__':
    app.run(debug=True)