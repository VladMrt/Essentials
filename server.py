import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
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

def search_products_in_db(keyword):
    conn = create_connection_products()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE name LIKE ? OR allergens LIKE ?", ('%' + keyword + '%', '%' + keyword + '%'))
    search_results = cursor.fetchall()
    conn.close()
    return search_results

@app.route('/search_product', methods = ['POST'])
def search_product():
    search_results = search_products_by_keyword(request.form['product'])
    
    approved_products = search_products_in_db(request.form['product'])

    all_products = search_results + approved_products

    cart_elements = len(session['cart'])
    if 'username' in session:
        loggedIn = True
        return render_template('search_product.html', search_results=all_products, username=session['username'], loggedIn=loggedIn, cart_elements=cart_elements)
    else:
        loggedIn = False
        return render_template('search_product.html', search_results=all_products, loggedIn=loggedIn, cart_elements=cart_elements)
    

@app.route('/product_details')
def product_details():
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
    
    soup = BeautifulSoup(html_content, 'html.parser')

    product_div = soup.find('div', class_='product-images')

    product_id = None 

    if product_div:
        product_link = product_div.find('a')
        if product_link:
            href = product_link.get('href')
            product_id = request.args.get('product_id') 
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
    
    api_url = f"https://world.openfoodfacts.org/api/v0/product/{product_id}.json"
    response = requests.get(api_url)
    if response.status_code == 200:
        product_data = response.json().get('product', {})
        allergens = product_data.get('allergens_tags', [])
        calories = product_data.get('nutriments', {}).get('energy-kcal_100g', 'N/A')
        
        fat = product_data.get('nutriments', {}).get('fat_100g', 'N/A')
        carbohydrates = product_data.get('nutriments', {}).get('carbohydrates_100g', 'N/A')
        proteins = product_data.get('nutriments', {}).get('proteins_100g', 'N/A')
        fiber = product_data.get('nutriments', {}).get('fiber_100g', 'N/A')
        sugar = product_data.get('nutriments', {}).get('sugars_100g', 'N/A')
        salt = product_data.get('nutriments', {}).get('salt_100g', 'N/A')
    else:
        allergens = []
        calories = 'N/A'
        fat = 'N/A'
        carbohydrates = 'N/A'
        proteins = 'N/A'
        fiber = 'N/A'
        sugar = 'N/A'
        salt = 'N/A'

    if 'username' in session:
        loggedIn = True
    else: loggedIn = False
    cart_elements = len(session['cart'])
    return render_template('product_details.html',product_id=product_id , name=name, ingredients=ingredients, nutrition=nutrition, image=image, loggedIn=loggedIn, username=session.get('username'), allergens=allergens, calories=calories, fat=fat, carbohydrates=carbohydrates, proteins=proteins, fiber=fiber, sugar=sugar, salt=salt, cart_elements=cart_elements)

#                       #
#  OPEN FOOD FACTS API  #
#          END          #

@app.route('/addToCart', methods=['POST'])
def addToCart():
    if request.form.get('item_id_product_details'):
        product_id = request.form.get('item_id_product_details')
        cart = session.get('cart', {})
        cart[product_id] = cart.get(product_id, 0) + 1
        session['cart'] = cart
        print(session['cart'])
        product = get_product_name(product_id)
        test = search_products_by_keyword(product)
        product = test[0]
        cart_elements = len(session['cart'])

        name = product.get('product_name')
        nutrition = product.get('nutrition_grades_tags')
        ingredients = product.get('ingredients_text')
        image = product.get('image_url')
    
        api_url = f"https://world.openfoodfacts.org/api/v0/product/{product_id}.json"
        response = requests.get(api_url)
        if response.status_code == 200:
            product_data = response.json().get('product', {})
            allergens = product_data.get('allergens_tags', [])
            calories = product_data.get('nutriments', {}).get('energy-kcal_100g', 'N/A')
            fat = product_data.get('nutriments', {}).get('fat_100g', 'N/A')
            carbohydrates = product_data.get('nutriments', {}).get('carbohydrates_100g', 'N/A')
            proteins = product_data.get('nutriments', {}).get('proteins_100g', 'N/A')
            fiber = product_data.get('nutriments', {}).get('fiber_100g', 'N/A')
            sugar = product_data.get('nutriments', {}).get('sugars_100g', 'N/A')
            salt = product_data.get('nutriments', {}).get('salt_100g', 'N/A')
        else:
            allergens = []
            calories = 'N/A'
            fat = 'N/A'
            carbohydrates = 'N/A'
            proteins = 'N/A'
            fiber = 'N/A'
            sugar = 'N/A'
            salt = 'N/A'

            if 'username' in session:
                loggedIn = True
            else: loggedIn = False

            return render_template('product_details.html',product_id=product_id , name=name, ingredients=ingredients, nutrition=nutrition, image=image, loggedIn=loggedIn, username=session.get('username'), allergens=allergens, calories=calories, fat=fat, carbohydrates=carbohydrates, proteins=proteins, fiber=fiber, sugar=sugar, salt=salt, cart_elements=cart_elements)
    else: 
        if request.form.get('item_id_product_search'):
            product_id = request.form.get('item_id_product_search')
            cart = session.get('cart', {})
            cart[product_id] = cart.get(product_id, 0) + 1
            session['cart'] = cart
            print(session['cart'])
            product = get_product_name(product_id)
            search_results = search_products_by_keyword(product)
            for item in search_results:
                print("Products:", item.get('product_name'))
            cart_elements = len(session['cart'])
            if 'username' in session:
                loggedIn = True
                return render_template('search_product.html', search_results=search_results, username=session['username'], loggedIn=loggedIn, cart_elements=cart_elements)
            else:
                loggedIn = False
                return render_template('search_product.html', search_results=search_results, loggedIn=loggedIn, cart_elements=cart_elements)
    
def fetch_nutritional_info(product_name):
    url = f"https://world.openfoodfacts.org/api/v0/product/{product_name}.json"
    response = requests.get(url)
    if response.status_code == 200:
        product_info = response.json()
        if 'product' in product_info:
            return product_info['product']
    return None

def analyze_nutritional_content(cart):
    total_nutrients = {
        'calories': 0,
        'fat': 0,
        'carbohydrates': 0,
        'proteins': 0,
        'fiber': 0,
        'sugar': 0,
        'salt': 0
    }

    for item, details in cart.items():
        product_info = fetch_nutritional_info(details['name'])
        if product_info:
            total_nutrients['calories'] += details['calories']
            total_nutrients['fat'] += product_info.get('nutriments', {}).get('fat_100g', 0)
            total_nutrients['carbohydrates'] += product_info.get('nutriments', {}).get('carbohydrates_100g', 0)
            total_nutrients['proteins'] += product_info.get('nutriments', {}).get('proteins', 0)
            total_nutrients['fiber'] += product_info.get('nutriments', {}).get('fiber_100g', 0)
            total_nutrients['sugar'] += product_info.get('nutriments', {}).get('sugars_100g', 0)
            total_nutrients['salt'] += product_info.get('nutriments', {}).get('salt_100g', 0)

    return total_nutrients

def recommend_similar_products(product_name):
    recommendations = []
    url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={product_name}&search_simple=1&action=process&json=1"
    response = requests.get(url)
    if response.status_code == 200:
        products = response.json().get('products', [])
        for product in products[:3]:  # Recommend top 3 similar products
            recommendations.append(product.get('product_name', 'Unknown'))

    return recommendations

@app.route('/viewCart')
def viewCart():
    cart = {}
    for item in session['cart']:
        product = get_product_name(item)
        test = search_products_by_keyword(product)
        product = test[0]
        api_url = f"https://world.openfoodfacts.org/api/v0/product/{item}.json"
        response = requests.get(api_url)
        product_data = response.json().get('product', {})
        cart[item] = {
            'id': item,
            'name': product.get('product_name'),
            'photo': product.get('image_url'),
            'allergens': product_data.get('allergens_tags', []),
            'calories': product_data.get('nutriments', {}).get('energy-kcal_100g', 'N/A'),
            'fat': product_data.get('nutriments', {}).get('fat_100g', 'N/A'),
            'carbohydrates': product_data.get('nutriments', {}).get('carbohydrates_100g', 'N/A'),
            'proteins': product_data.get('nutriments', {}).get('proteins', 'N/A'),
            'fiber': product_data.get('nutriments', {}).get('fiber_100g', 'N/A'),
            'sugar': product_data.get('nutriments', {}).get('sugars_100g', 'N/A'),
            'salt': product_data.get('nutriments', {}).get('salt_100g', 'N/A')
        }
        
    cart_lenght = len(session['cart'])

    #Recomandations
    total_nutrients = analyze_nutritional_content(cart)
    recommendations = {}
    for nutrient_category in total_nutrients.keys():
        recommendations[nutrient_category] = recommend_similar_products(nutrient_category)
    
    print(recommendations)

    if 'username' in session:
        loggedIn = True
        return render_template('cart.html', cart=cart, cart_lenght=cart_lenght, loggedIn=loggedIn, username=session['username'], recommendations=recommendations)
    else: 
        loggedIn = False
        return render_template('cart.html', cart=cart, cart_lenght=cart_lenght, loggedIn=loggedIn, recommendations=recommendations)
    
def create_connection_users():
    conn = None
    try:
        conn = sqlite3.connect('user_credentials.sql')
        print("Connection to SQLite DB successful")
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite DB: {e}")
    return conn

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
                admin INTEGER NOT NULL
            )
        """)
        print("Users table created successfully!")
    except sqlite3.Error as e:
        print(f"Error creating users table: {e}")


def create_table_products(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                photo TEXT,
                allergens TEXT,
                calories TEXT,
                fat TEXT,
                carbohydrates TEXT,
                proteins TEXT,
                fiber TEXT,
                sugar TEXT,
                salt TEXT,
                approved INTEGER NOT NULL
            )
        ''')
        conn.commit()
        print("Table 'products' Created Successfully")
    except sqlite3.Error as e:
        print(e)

def create_connection_products():
    conn = None
    try:
        conn = sqlite3.connect('products.sql')
        print("SQLite Database Connection Established")
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

@app.route('/new_product_action', methods=['POST'])
def new_product_action():
    if request.method == 'POST':
        name = request.form['name']
        photo = request.form['photo']
        allergens = request.form['allergens']
        calories = request.form['calories']
        fat = request.form['fat']
        carbohydrates = request.form['carbohydrates']
        proteins = request.form['proteins']
        fiber = request.form['fiber']
        sugar = request.form['sugar']
        salt = request.form['salt']
        approved = 0

        conn = create_connection_products()
        cursor = conn.cursor()

        cursor.execute('''
                SELECT * FROM products
                WHERE name = ? AND photo = ? AND allergens = ? AND calories = ?
                AND fat = ? AND carbohydrates = ? AND proteins = ? AND fiber = ?
                AND sugar = ? AND salt = ?
            ''', (name, photo, allergens, calories, fat, carbohydrates, proteins, fiber, sugar, salt))
        duplicate_products = cursor.fetchall()
        if len(duplicate_products) >= 2:
            approved = 1
        
        try:
            cursor.execute('''
                INSERT INTO products (name, photo, allergens, calories, fat, carbohydrates, proteins, fiber, sugar, salt, approved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, photo, allergens, calories, fat, carbohydrates, proteins, fiber, sugar, salt, approved))
            conn.commit()
            print("Product added successfully.")
        except sqlite3.Error as e:
            print("Error adding product:", e)
        finally:
            conn.close()

        return home()

       
@app.route('/new_product')
def new_product():
    if 'username' in session:
        username = session['username']
        loggedIn = True
    else: loggedIn = False
    return render_template('submit_new_product.html', username=username, loggedIn=loggedIn)

@app.route('/check_submissions')
def check_subsmissions():
    if 'username' in session:
        username = session['username']
        loggedIn = True
    else: loggedIn = False
    conn = create_connection_products()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        print("Products:", products)
        return render_template('submissions.html', products=products, username=username, loggedIn=loggedIn)
    except sqlite3.Error as e:
        print("Error retrieving products:", e)
    finally:
        conn.close()

def update_product_approval(product_id):
    with create_connection_products() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET approved = 1 WHERE id = ?", (product_id,))
        conn.commit()

@app.route('/submit_product', methods=['POST'])
def submit_product():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        
        update_product_approval(product_id)
        
        return home()

def printDB():
    conn = create_connection_users()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    conn.close()
    print("Data in the users table:")
    for row in rows:
        print(row)
    
    conn = create_connection_products()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    conn.close()
    print("Data in the products table:")
    for row in rows:
        print(row)

conn = create_connection_users()
create_users_table(conn)
conn.close()

conn = create_connection_products()
create_table_products(conn)
conn.close()

printDB()

def create_connection_users():
    conn = None
    try:
        conn = sqlite3.connect('user_credentials.sql')
        print("SQLite Database Connection Established")
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

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
        admin = 0
        conn = create_connection_users()

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            printDB()
            return render_template('registerUserAlreadyExists.html', username=username)
        else:
            try:
                cursor.execute("INSERT INTO users (username, password, firstName, lastName, email, dietary_preferences, allergens, admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (username, password, firstName, lastName, email, dietary_preferences, allergens, admin))
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
    username = request.form['username']
    password = request.form['password']

    conn = create_connection_users()

    create_users_table(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        if password == existing_user[2]:
            conn.close()
            printDB()
            session['username'] = username
            return home()
        else:
            conn.close()
            flash('Incorrect username or password. Please try again.', 'error')
            printDB()
            return render_template('login.html')

    else:
        return 'Method not allowed'

@app.route('/logout_action')
def logOut():
    session.clear()
    return render_template('redirect.html')

@app.route('/change_info_action')
def changeInfo():
    new_firstName = request.form['newFirstName']
    new_lastName = request.form['newLastName']
    new_username = request.form['newUsername']
    new_allergens = request.form['newAllergens']
    new_dietary_preferences = request.form['newDietary_preferences']
    new_allergens = request.form['newAllergens']
    new_approved = 0
        
    # Check if the user is logged in
    if 'username' in session:
        username = session['username']
            
        # Connect to the database
        conn = create_connection_users()
        cursor = conn.cursor()
            
        try:
            # Update the user's information in the database
            cursor.execute("UPDATE users SET firstName=?, lastName=?, username=?, allergens=?, dietary_preferences=?, approved=? WHERE username=?", 
                            (new_firstName, new_lastName, new_username, new_allergens, new_dietary_preferences, new_approved, username))
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
    cart_elements = len(session['cart'])
    if 'username' in session:
        username = session['username']

        conn = create_connection_users()
        cursor = conn.cursor()

        cursor.execute("SELECT firstName, lastName, username, allergens, dietary_preferences FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()  # Fetch the first row
        if user_data:
            firstName, lastName, username, allergens, dietary_preferences = user_data
            print(firstName)
            print(lastName)
            print(username)
            print(allergens)
            print(dietary_preferences)

            return render_template('myaccount.html', firstName=firstName, lastName=lastName, username=username, allergens=allergens, dietary_preferences=dietary_preferences, cart_elements=cart_elements)

@app.route('/')
def home():
    admin = False

    if 'cart' not in session:
        session['cart'] = {}
    cart_elements = len(session['cart'])
    if 'username' in session:
        loggedIn = True
        username = session['username']
        conn = create_connection_users()
        create_users_table(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            if existing_user[8] == 1:
                admin = True
        return render_template('home.html', username=session['username'], loggedIn=loggedIn, cart_elements=cart_elements, admin=admin)
    else:
        return render_template('home.html', loggedIn=False, cart_elements=cart_elements, admin=admin)

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
