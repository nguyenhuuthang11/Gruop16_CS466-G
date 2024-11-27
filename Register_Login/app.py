from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from flask_login import LoginManager, login_required, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Khởi tạo ứng dụng Flask
app = Flask(__name__, template_folder='Template')

# Thiết lập khóa bí mật để mã hóa dữ liệu phiên người dùng
app.secret_key = 'xyzsdfg'

# Cấu hình kết nối MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'men1905@'
app.config['MYSQL_DB'] = 'usermanagement'

# Tạo kết nối MySQL
mysql = MySQL(app)

# Decorator để kiểm tra vai trò người dùng
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'loggedin' not in session or session.get('role') != required_role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Route cho trang đăng nhập
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            message = 'Logged in successfully!'
            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif session['role'] == 'manager':
                return redirect(url_for('manager_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            message = 'Invalid email or password!'
    return render_template('login.html', message=message)

# Route cho chức năng đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form:
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        role = request.form.get('role', 'user')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        account = cursor.fetchone()

        if account:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                'INSERT INTO user (name, email, password, role) VALUES (%s, %s, %s, %s)',
                (userName, email, hashed_password, role)
            )
            mysql.connection.commit()
            message = 'You have successfully registered!'
            return redirect(url_for('login'))
    return render_template('register.html', message=message)

# Route cho dashboard admin
@app.route('/admin_dashboard')
@role_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html', message='Welcome, Admin!')

# Route cho dashboard manager
@app.route('/manager_dashboard')
@role_required('manager')
def manager_dashboard():
    return render_template('manager_dashboard.html', message='Welcome, Manager!')

# Route cho dashboard user
@app.route('/user_dashboard')
@role_required('user')
def user_dashboard():
    return render_template('user_dashboard.html', message='Welcome, User!')

# Route cho chức năng đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Chạy ứng dụng
if __name__ == "__main__":
    app.run(debug=True)
