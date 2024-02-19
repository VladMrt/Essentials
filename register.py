import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

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
    return render_template('register.html')

# Route to handle form submission and store data in the database
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to the database
        conn = create_connection()

        # Create the users table if it doesn't exist
        create_users_table(conn)

        # Insert data into the users table
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            message = "Data inserted successfully"
        except sqlite3.Error as e:
            conn.rollback()
            message = f"Error inserting data: {e}"
        finally:
            conn.close()

        # Retrieve and print data from the users table
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        conn.close()
        print("Data in the users table:")
        for row in rows:
            print(row)

        return message
    else:
        return 'Method not allowed'

if __name__ == '__main__':
    app.run(debug=True)
