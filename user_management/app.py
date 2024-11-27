from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Kết nối cơ sở dữ liệu SQLite
def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Tạo bảng users nếu chưa có
def create_table():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        email TEXT,
                        role TEXT)''')
    conn.commit()

create_table()
def create_content_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS some_content_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

def insert_sample_content():
    conn = get_db()
    conn.execute('''
        INSERT INTO some_content_table (content)
        VALUES 
        ('Nội dung mẫu 1'),
        ('Nội dung mẫu 2'),
        ('Nội dung mẫu 3')
    ''')
    conn.commit()

# Gọi các hàm tạo bảng và thêm dữ liệu
create_content_table()

# Chỉ gọi hàm thêm dữ liệu trong quá trình phát triển
# insert_sample_content()


# Trang chủ (hiển thị trang đăng nhập)
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            # Log kiểm tra vai trò
            print(f"Đăng nhập thành công: {user['username']} với vai trò {user['role']}")

            flash('Đăng nhập thành công', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng', 'danger')

    return render_template('login.html')


# Trang đăng kí
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        role = request.form['role']

        conn = get_db()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if existing_user:
            flash('Tên đăng nhập đã tồn tại', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        conn.execute('INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                     (username, hashed_password, email, role))
        conn.commit()
        flash('Đăng ký thành công', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Bạn cần đăng nhập để truy cập vào trang này.', 'danger')
        return redirect(url_for('home'))

    role = session.get('role')

    if role == 'admin':
        conn = get_db()
        users = conn.execute('SELECT * FROM users').fetchall()
        return render_template('admin_dashboard.html', users=users)

    elif role == 'content_manager':  # Vai trò quản lý nội dung
        conn = get_db()
        content = conn.execute('SELECT * FROM some_content_table').fetchall()
        return render_template('manager_dashboard.html', content=content)

    elif role == 'user':
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        return render_template('user_dashboard.html', user=user)

    else:
        flash('Vai trò người dùng không hợp lệ.', 'danger')
        return redirect(url_for('home'))



# Chỉnh sửa người dùng
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Bạn không có quyền truy cập vào trang này.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if user is None:
        flash('Không tìm thấy người dùng này.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        role = request.form['role']

        conn.execute('UPDATE users SET username = ?, email = ?, role = ? WHERE id = ?',
                     (username, email, role, user_id))
        conn.commit()
        flash('Thông tin người dùng đã được cập nhật.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_user.html', user=user)

# Đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    flash('Đăng xuất thành công', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
