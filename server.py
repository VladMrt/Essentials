import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'albinute'

# Function to create a database connection
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('user_credentials.db')
        print("Connection to SQLite DB successful")
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite DB: {e}")
    return conn

# Function to create the users table if it doesn't exist
def create_users_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)
        print("Users table created successfully")
    except sqlite3.Error as e:
        print(f"Error creating users table: {e}")

# Route to render the HTML form
@app.route('/')
def home():
    return render_template('home.html')

# Route to render the registration form
@app.route('/register')
def register():
    return render_template('register.html')

# Route to render the login form
@app.route('/login')
def login():
    return render_template('login.html')

def printDB():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()
    print("Data in the users table:")
    for row in rows:
        print(row)

# Route to handle registration submission and store data in the database
@app.route('/register_action', methods=['POST'])
def register_action():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to the database
        conn = create_connection()

        # Create the users table if it doesn't exist
        create_users_table(conn)

        # Check if the username already exists
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            printDB()
            return render_template('registerUserAlreadyExists.html', username=username)
        else:
            try:
                # Insert data into the users table
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                message = "Data inserted successfully"
            except sqlite3.Error as e:
                conn.rollback()
                message = f"Error inserting data: {e}"
            finally:
                conn.close()

            printDB()

            return render_template('redirect.html')
    else:
        return 'Method not allowed'
    
# Route to handle login submissions and verify the data in the database
@app.route('/login_action', methods=['POST'])
def login_action():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to the database
        conn = create_connection()

        # Create the users table if it doesn't exist
        create_users_table(conn)

        # Check if the username exists and the password matches
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            # If the username exists, check if the password matches
            if password == existing_user[2]:
                conn.close()
                printDB()
                return render_template('homeLoggedIn.html', username=username)
            else:
                conn.close()
                flash('Incorrect password. Please try again.', 'error')
                printDB()
                return render_template('login.html')
        else:
            conn.close()
            flash('Username not found. Please register.', 'error')
            printDB()
            return render_template('register.html')
    else:
        return 'Method not allowed'

# Redirect route
@app.route('/redirect')
def redirect():
    return render_template('redirect.html')

if __name__ == '__main__':
    app.run(debug=True)
