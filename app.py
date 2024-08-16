from flask import Flask, request, jsonify, render_template, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)


# Endpoint to show list of books and their status
@app.route('/')
def show_books():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('SELECT * FROM Books')
    books = c.fetchall()
    conn.close()
    return render_template('show_books.html', books=books)

@app.route('/show_members')
def show_members():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # קבלת כל הממברים
    c.execute('SELECT * FROM Members')
    members = c.fetchall()
    
    # קבלת כל הספרים שהושאלו ושלא הוחזרו כולל תאריך ההשאלה
    c.execute('''
    SELECT Members.member_id, Members.name, Books.title, Loans.loan_date 
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
        
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute('INSERT INTO Books (title, author, published_year, available) VALUES (?, ?, ?, 1)', (title, author, published_year))
        conn.commit()
        conn.close()
        
        return redirect(url_for('show_books'))
    return render_template('add_book.html')

# Endpoint to add a member
@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        member_details = request.form
        name = member_details['name']
        
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute('INSERT INTO Members (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
        
        return redirect(url_for('show_books'))
    return render_template('add_member.html')

# Endpoint to loan a book
from datetime import datetime, timedelta

@app.route('/loan_book', methods=['GET', 'POST'])
def loan_book():
    if request.method == 'POST':
        loan_details = request.form
        book_id = loan_details['book_id']
        member_id = loan_details['member_id']
        loan_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        due_date = (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute('UPDATE Books SET available = 0 WHERE book_id = ?', (book_id,))
        c.execute('INSERT INTO Loans (book_id, member_id, loan_date, due_date) VALUES (?, ?, ?, ?)', 
                  (book_id, member_id, loan_date, due_date))
        conn.commit()
        conn.close()
        
        return redirect(url_for('show_books'))
    
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('SELECT * FROM Books WHERE available = 1')
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
        
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute('SELECT due_date FROM Loans WHERE loan_id = ?', (loan_id,))
        due_date = c.fetchone()[0]
        
        if datetime.strptime(return_date, '%Y-%m-%d %H:%M:%S') > datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S'):
            # ספר מוחזר באיחור - ניתן להוסיף כאן קוד לטיפול במקרים כאלה
            print("The book was returned late")

        c.execute('UPDATE Loans SET return_date = ? WHERE loan_id = ?', (return_date, loan_id))
        c.execute('UPDATE Books SET available = 1 WHERE book_id = (SELECT book_id FROM Loans WHERE loan_id = ?)', (loan_id,))
        conn.commit()
        conn.close()
        
        return redirect(url_for('show_books'))
    
    conn = sqlite3.connect('library.db')
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
    conn = sqlite3.connect('library.db')
    c = conn.cursor()

    if request.method == 'POST':
        updated_details = request.form
        title = updated_details['title']
        author = updated_details['author']
        published_year = updated_details['published_year']
        c.execute('UPDATE Books SET title = ?, author = ?, published_year=?  WHERE book_id = ?', (title, author,published_year , book_id))
        conn.commit()
        conn.close()
        return redirect(url_for('show_books'))

    c.execute('SELECT * FROM Books WHERE book_id = ?', (book_id,))
    book = c.fetchone()
    conn.close()

    return render_template('update_book.html', book=book)


@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('DELETE FROM Books WHERE book_id = ?', (book_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('show_books'))

@app.route('/update_member/<int:member_id>', methods=['GET', 'POST'])
def update_member(member_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()

    if request.method == 'POST':
        updated_details = request.form
        name = updated_details['name']
        c.execute('UPDATE Members SET name = ? WHERE member_id = ?', (name, member_id))
        conn.commit()
        conn.close()
        return redirect(url_for('show_members'))

    c.execute('SELECT * FROM Members WHERE member_id = ?', (member_id,))
    member = c.fetchone()
    conn.close()

    return render_template('update_member.html', member=member)


@app.route('/delete_member/<int:member_id>', methods=['POST'])
def delete_member(member_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute('DELETE FROM Members WHERE member_id = ?', (member_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('show_members'))

@app.route('/search_books', methods=['GET', 'POST'])
def search_books():
    query = ''
    books = []
    
    if request.method == 'POST':
        query = request.form['query']
        
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute('''
            SELECT * FROM Books
            WHERE title LIKE ? OR author LIKE ?
        ''', ('%' + query + '%', '%' + query + '%'))
        books = c.fetchall()
        conn.close()
    
    return render_template('search_books.html', query=query, books=books)

@app.route('/statistics')
def statistics():
    conn = sqlite3.connect('library.db')
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
    c.execute('SELECT COUNT(*) FROM Books WHERE available = 1')
    available_books = c.fetchone()[0]

    conn.close()

    return render_template('statistics.html', total_books=total_books, loaned_books=loaned_books, total_members=total_members, available_books=available_books)



if __name__ == '__main__':
    app.run(debug=True)