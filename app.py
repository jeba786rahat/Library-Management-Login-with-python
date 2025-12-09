from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3, datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / 'library.db'

app = Flask(__name__)
app.secret_key = 'dev-secret-key'

FINE_PER_DAY = 5  # assumption
MAX_BOOKS_PER_USER = 3  # assumption
DEFAULT_ISSUE_DAYS = 15

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def current_date_str():
    return datetime.date.today().isoformat()

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username=? AND password=?', (username,password)).fetchone()
        conn.close()
        if user:
            session['user'] = dict(user)
            flash('Logged in as ' + username)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out')
    return redirect(url_for('login'))

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user' not in session or session['user']['role'] != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrapped

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Maintenance: Add Book
@app.route('/maintenance/books/add', methods=['GET','POST'])
@login_required
@admin_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        author = request.form.get('author','').strip()
        serial = request.form.get('serial','').strip()
        if not title or not author or not serial:
            flash('All fields mandatory', 'error')
            return render_template('add_book.html', form=request.form)
        conn = get_db()
        try:
            conn.execute('INSERT INTO books (title,author,serial_no,available) VALUES (?,?,?,1)', (title,author,serial))
            conn.commit()
            flash('Book added')
            return redirect(url_for('list_books'))
        except Exception as e:
            flash('Error: ' + str(e), 'error')
        finally:
            conn.close()
    return render_template('add_book.html')

@app.route('/maintenance/books')
@login_required
@admin_required
def list_books():
    conn = get_db()
    books = conn.execute('SELECT * FROM books').fetchall()
    conn.close()
    return render_template('list_books.html', books=books)

# Maintenance: Add Member
@app.route('/maintenance/members/add', methods=['GET','POST'])
@login_required
@admin_required
def add_member():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        member_no = request.form.get('member_no','').strip()
        phone = request.form.get('phone','').strip()
        email = request.form.get('email','').strip()
        plan = request.form.get('plan','6')
        if not name or not member_no:
            flash('Name and Membership Number mandatory', 'error')
            return render_template('add_member.html', form=request.form)
        start = datetime.date.today()
        if plan == '6':
            end = start + datetime.timedelta(days=182)
        elif plan == '12':
            end = start + datetime.timedelta(days=365)
        else:
            end = start + datetime.timedelta(days=365*2)
        conn = get_db()
        try:
            conn.execute('INSERT INTO members (member_no,name,phone,email,address,start_date,end_date) VALUES (?,?,?,?,?,?,?)',
                         (member_no,name,phone,email,request.form.get('address',''), start.isoformat(), end.isoformat()))
            conn.commit()
            flash('Member added')
            return redirect(url_for('list_members'))
        except Exception as e:
            flash('Error: ' + str(e), 'error')
        finally:
            conn.close()
    return render_template('add_member.html')

@app.route('/maintenance/members')
@login_required
@admin_required
def list_members():
    conn = get_db()
    members = conn.execute('SELECT * FROM members').fetchall()
    conn.close()
    return render_template('list_members.html', members=members)

# Transactions: Search available books and Issue
@app.route('/transactions/issue', methods=['GET','POST'])
@login_required
def issue_book():
    conn = get_db()
    if request.method == 'POST':
        serial = request.form.get('serial','').strip()
        member_no = request.form.get('member_no','').strip()
        if not (serial or request.form.get('book_id')):
            flash('Please select a book (serial or select from results)', 'error')
            return redirect(url_for('issue_book'))
        # allow either serial or selected book id
        book = None
        if request.form.get('book_id'):
            book = conn.execute('SELECT * FROM books WHERE id=?', (request.form.get('book_id'),)).fetchone()
        else:
            book = conn.execute('SELECT * FROM books WHERE serial_no=?', (serial,)).fetchone()
        if not book:
            flash('Book not found', 'error')
            conn.close()
            return redirect(url_for('issue_book'))
        if book['available'] == 0:
            flash('Book not available', 'error')
            conn.close()
            return redirect(url_for('issue_book'))
        member = conn.execute('SELECT * FROM members WHERE member_no=?', (member_no,)).fetchone()
        if not member:
            flash('Member not found', 'error')
            conn.close()
            return redirect(url_for('issue_book'))
        # check membership active
        if member['end_date'] < current_date_str():
            flash('Membership expired', 'error')
            conn.close()
            return redirect(url_for('issue_book'))
        # check user's current issued count
        issued_count = conn.execute('SELECT COUNT(*) as c FROM issues WHERE member_id=? AND actual_return_date IS NULL', (member['id'],)).fetchone()['c']
        if issued_count >= MAX_BOOKS_PER_USER:
            flash('Member has reached max issued books', 'error')
            conn.close()
            return redirect(url_for('issue_book'))
        issue_date = datetime.date.today()
        return_date = issue_date + datetime.timedelta(days=DEFAULT_ISSUE_DAYS)
        conn.execute('INSERT INTO issues (book_id,member_id,issue_date,return_date) VALUES (?,?,?,?)',
                     (book['id'], member['id'], issue_date.isoformat(), return_date.isoformat()))
        conn.execute('UPDATE books SET available=0 WHERE id=?', (book['id'],))
        conn.commit()
        conn.close()
        flash('Book issued successfully')
        return redirect(url_for('dashboard'))
    # GET -> show searchable available books
    books = conn.execute('SELECT * FROM books WHERE available=1').fetchall()
    conn.close()
    return render_template('issue_book.html', books=books)

# Transactions: Return Book
@app.route('/transactions/return', methods=['GET','POST'])
@login_required
def return_book():
    conn = get_db()
    if request.method == 'POST':
        issue_id = request.form.get('issue_id')
        if not issue_id:
            flash('Select an issued book row to return', 'error')
            conn.close()
            return redirect(url_for('return_book'))
        issue = conn.execute('SELECT * FROM issues WHERE id=?', (issue_id,)).fetchone()
        if not issue:
            flash('Issue record not found', 'error')
            conn.close()
            return redirect(url_for('return_book'))
        # calculate fine
        actual_return = datetime.date.today()
        due = datetime.date.fromisoformat(issue['return_date'])
        delta = (actual_return - due).days
        fine = FINE_PER_DAY * delta if delta > 0 else 0
        paid = 1 if request.form.get('fine_paid')=='on' else 0
        if fine > 0 and not paid:
            flash('Fine pending: please mark fine as paid to complete return', 'error')
            conn.close()
            return redirect(url_for('return_book'))
        # complete return
        conn.execute('UPDATE issues SET actual_return_date=?, fine_paid=?, remarks=? WHERE id=?',
                     (actual_return.isoformat(), paid, request.form.get('remarks',''), issue_id))
        conn.execute('UPDATE books SET available=1 WHERE id=?', (issue['book_id'],))
        conn.commit()
        conn.close()
        flash('Book return processed')
        return redirect(url_for('dashboard'))
    # show issued books
    issues = conn.execute('SELECT issues.*, books.title, books.serial_no, members.member_no FROM issues JOIN books ON issues.book_id=books.id JOIN members ON issues.member_id=members.id WHERE issues.actual_return_date IS NULL').fetchall()
    conn.close()
    return render_template('return_book.html', issues=issues)

# Reports
@app.route('/reports/available')
@login_required
def report_available():
    conn = get_db()
    books = conn.execute('SELECT * FROM books WHERE available=1').fetchall()
    conn.close()
    return render_template('report_available.html', books=books)

@app.route('/reports/issued')
@login_required
def report_issued():
    conn = get_db()
    issues = conn.execute('SELECT issues.*, books.title, books.serial_no, members.member_no FROM issues JOIN books ON issues.book_id=books.id JOIN members ON issues.member_id=members.id').fetchall()
    conn.close()
    return render_template('report_issued.html', issues=issues)

@app.route('/reports/overdue')
@login_required
def report_overdue():
    conn = get_db()
    today = current_date_str()
    issues = conn.execute("SELECT issues.*, books.title, members.member_no FROM issues JOIN books ON issues.book_id=books.id JOIN members ON issues.member_id=members.id WHERE issues.actual_return_date IS NULL AND issues.return_date < ?", (today,)).fetchall()
    conn.close()
    return render_template('report_overdue.html', issues=issues)






# 📌 Update Book via Modal
@app.route('/maintenance/books/modal/update', methods=['POST'])
@admin_required
@login_required
def update_book_modal():
    book_id = request.form['id']
    title = request.form['title']
    author = request.form['author']
    serial_no = request.form['serial_no']

    try:
        with get_db() as conn:
            conn.execute("""
                UPDATE books SET title=?, author=?, serial_no=? WHERE id=?
            """, (title, author, serial_no, book_id))
            conn.commit()

        flash("Book updated successfully!", "success")

    except Exception as e:
        flash("Error updating book!", "danger")
        print(e)

    return redirect(url_for("list_books"))


# 📌 Delete Book via Modal
@app.route('/maintenance/books/modal/delete', methods=['POST'])
@admin_required
@login_required
def delete_book_modal():
    book_id = request.form['id']

    try:
        with get_db() as conn:
            conn.execute("DELETE FROM books WHERE id=?", (book_id,))
            conn.commit()

        flash("Book deleted successfully!", "danger")

    except Exception as e:
        flash("Error deleting book!", "danger")
        print(e)

    return redirect(url_for("list_books"))





@app.route('/maintenance/members/modal/update', methods=['POST'])
def update_member():
    member_id = request.form.get('id')
    member_no = request.form.get('member_no')
    name = request.form.get('name')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        UPDATE members
        SET member_no = ?, name = ?, start_date = ?, end_date = ?
        WHERE id = ?
    """, (member_no, name, start_date, end_date, member_id))

    conn.commit()
    conn.close()

    flash("Member updated successfully!", "success")
    return redirect(url_for('list_members'))

@app.route('/maintenance/members/modal/delete', methods=['POST'])
def delete_member():
    member_id = request.form.get('id')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()

    flash("Member deleted successfully!", "success")
    return redirect(url_for('list_members'))





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
