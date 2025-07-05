from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import User, get_db_connection
from forms import LoginForm, RegisterForm, ExpenseForm
import pandas as pd

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['password'])
    return None

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                       (form.username.data, form.password.data))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s",
                       (form.username.data, form.password.data))
        user = cursor.fetchone()
        conn.close()
        if user:
            login_user(User(user['id'], user['username'], user['password']))
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials")
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = ExpenseForm()
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if form.validate_on_submit():
        cursor.execute("INSERT INTO expenses (user_id, description, amount) VALUES (%s, %s, %s)",
                       (current_user.id, form.description.data, form.amount.data))
        conn.commit()

    cursor.execute("SELECT * FROM expenses WHERE user_id = %s", (current_user.id,))
    expenses = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', form=form, expenses=expenses)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = %s AND user_id = %s", (id, current_user.id))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/export')
@login_required
def export():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM expenses WHERE user_id = %s", (current_user.id,))
    data = cursor.fetchall()
    df = pd.DataFrame(data)
    file_path = f"exports/expenses_user_{current_user.id}.xlsx"
    df.to_excel(file_path, index=False)
    conn.close()
    return send_file(file_path, as_attachment=True)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
