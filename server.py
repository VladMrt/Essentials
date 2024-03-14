import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from openfoodfacts import API, APIVersion, Country, Environment, Flavor
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'albinute'

#                       #
#  OPEN FOOD FACTS API  #
#        START          #

api = API(
    # user_agent="MyWebApp/1.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    username=None,
    password=None,
    country=Country.world,
    flavor=Flavor.off,
    version=APIVersion.v2,
    environment=Environment.org,
)

def search_products_by_keyword(keyword):
    base_url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": keyword,
        "page_size": 5,
        "json": 1
    }
    
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        search_results = response.json()
        return search_results.get('products', [])
    else:
        print("Error:", response.status_code)
        return []

def get_product_name(product_id):
    url = f"https://world.openfoodfacts.org/api/v0/product/{product_id}.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'product' in data and 'product_name' in data['product']:
            return data['product']['product_name']
    return None

@app.route('/search_product', methods = ['POST'])
def search_product():
    search_results = search_products_by_keyword(request.form['product'])
    for item in search_results:
        print("Products:", item.get('product_name'))
    # if search_results:
    #     products = search_results['products']
    #     if products:
    #         product = products[0]
    #         name = product.get('product_name')
    #         nutrition = product.get('nutrition_grades_tags')
    #         ingredients = product.get('ingredients_text')
    #         image = product.get('image_url')
    #         print("Product Name:", name)
    #         print("Ingredients:", nutrition)
    #         print("Nutrition Facts:", ingredients)
    #         return render_template('product.html', name=name, ingredients=ingredients, nutrition=nutrition, image=image)
    #     else:
    #         print("No products found with the given name.")
    #         return render_template('test_off_api.html')
    return render_template('search_product.html', search_results=search_results)
    

@app.route('/product_details')
def product_details():
    # Assuming you have the HTML content passed from a request or stored somewhere
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>test</title>
    </head>
    <body>
        <h1>L</h1>
        <p>aaaaaaaaaaaaa</p>
        <div class="product-images">
            {% for product in search_results %}
                <a href='/product_details?product_id={{ product.product_id }}'>
                <img src="{{ product.image_url }}" alt="{{ product.product_name }}">
            </a>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the product div
    product_div = soup.find('div', class_='product-images')

    product_id = None  # Initialize product_id to None

    # Extract product ID from the href attribute of the anchor tag
    if product_div:
        product_link = product_div.find('a')  # Find the first anchor tag within the product div
        if product_link:
            href = product_link.get('href')
            product_id = request.args.get('product_id')  # Extract product_id from the href query parameter
            print("Product ID:", product_id)
        else:
            print("Product link not found")
    else:
        print("Product div not found")
    
    product = get_product_name(product_id)
    test = search_products_by_keyword(product)
    product = test[0]

    name = product.get('product_name')
    nutrition = product.get('nutrition_grades_tags')
    ingredients = product.get('ingredients_text')
    image = product.get('image_url')

    if 'username' in session:
        loggedIn = True
    else: loggedIn = False

    return render_template('product_details.html', name=name, ingredients=ingredients, nutrition=nutrition, image=image, loggedIn=loggedIn)


#                       #
#  OPEN FOOD FACTS API  #
#          END          #


# Function to create a database connection
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('user_credentials.sql')
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
                password TEXT NOT NULL,
                firstName TEXT NOT NULL,
                lastName TEXT NOT NULL,
                email TEXT NOT NULL,
                dietary_preferences TEXT NOT NULL,
                allergens TEXT NOT NULL,
                avatar TEXT NOT NULL
            )
        """)
        print("Users table created successfully!")
    except sqlite3.Error as e:
        print(f"Error creating users table: {e}")

# Route to render the home page
@app.route('/')
def home():
    if 'username' in session:
        loggedIn = True
        return render_template('home.html', username=session['username'], loggedIn=loggedIn)
    else:
        return render_template('home.html', loggedIn=False)

# Route to render the registration page
@app.route('/register')
def register():
    return render_template('register.html')

# Route to render the login page
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

conn = create_connection()
create_users_table(conn)
printDB()
conn.close()

# Route to handle registration submission and store data in the database
@app.route('/register_action', methods=['POST'])
def register_action():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        email = request.form['email']
        dietary_preferences = request.form['dietary_preferences']
        allergens = request.form['allergens']
        avatar = request.form['avatar']

        conn = create_connection()

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
                cursor.execute("INSERT INTO users (username, password, firstName, lastName, email, dietary_preferences, allergens, avatar) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (username, password, firstName, lastName, email, dietary_preferences, allergens, avatar))
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
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
                session['username'] = username
                return render_template('home.html', username=username, loggedIn = True)
            else:
                conn.close()
                flash('Incorrect username or password. Please try again.', 'error')
                printDB()
                return render_template('login.html')

    else:
        return 'Method not allowed'

#Log out function
@app.route('/logout_action')
def logOut():
    session.clear()
    return render_template('redirect.html')

#Change profile info
@app.route('/change_info_action', methods=['POST'])
def changeInfo():
    # Extract new information from the form
    new_firstName = request.form['newFirstName']
    new_lastName = request.form['newLastName']
    new_username = request.form['newUsername']
    new_allergens = request.form['newAllergens']
    new_dietary_preferences = request.form['newDietary_preferences']
    new_allergens = request.form['newAllergens']
    new_avatar = request.form['newAvatar']
        
    # Check if the user is logged in
    if 'username' in session:
        username = session['username']
            
        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()
            
        try:
            # Update the user's information in the database
            cursor.execute("UPDATE users SET firstName=?, lastName=?, username=?, allergens=?, dietary_preferences=?, avatar=? WHERE username=?", 
                            (new_firstName, new_lastName, new_username, new_allergens, new_dietary_preferences, new_avatar, username))
            conn.commit()
            message = "User information updated successfully"
            print(message)
            printDB()
        except sqlite3.Error as e:
            conn.rollback()
            message = f"Error updating user information: {e}"
        finally:
            conn.close()
    return myaccount()

# Redirect route
@app.route('/redirect')
def redirect():
    return render_template('redirect.html')

# My account route
@app.route('/myaccount')
def myaccount():
    if 'username' in session:
        # Get the username from the session
        username = session['username']

        # Connect to the database
        conn = create_connection()
        cursor = conn.cursor()

        # Retrieve user information from the database based on the username
        cursor.execute("SELECT firstName, lastName, username, allergens, dietary_preferences, avatar FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()  # Fetch the first row
        if user_data:
            # Unpack the user data
            firstName, lastName, username, allergens, dietary_preferences, avatar = user_data
            print(firstName)
            print(lastName)
            print(username)
            print(allergens)
            print(dietary_preferences)

            # Render the template with user data
            return render_template('myaccount.html', firstName=firstName, lastName=lastName, username=username, allergens=allergens, dietary_preferences=dietary_preferences, avatar=avatar)
        
if __name__ == '__main__':
    app.run(debug=True)
