from flask import Flask, request, render_template, session, flash, url_for,redirect, logging
from passlib.hash import sha256_crypt
from functools import wraps
from flask_mysqldb import MySQL
import yaml

app = Flask(__name__)

db = yaml.load(open('db.yaml'))
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = 'thhytygfg54t342fes'
mysql = MySQL(app)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login_page'))
    return wrap

#logout
@app.route("/logout/")
@login_required
def logout():
    session.clear()
    flash("You have been logged out!")
    return redirect(url_for('index') )

#index
@app.route("/")
def index():
    return render_template("index.html")
    
#about
@app.route("/about")
def about():
    return render_template('about.html')

#books
@app.route("/books")
def books():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get books
    result = cur.execute("SELECT * FROM books") 
    if result > 0:
        books = cur.fetchall()
        return render_template('books.html', books=books)
        # Close connection
        cur.close()    
    else:
        msg = 'No books Found'
        return render_template('books.html', msg=msg)
    
#Single Book
@app.route('/books/<string:bid>/')
def book(bid):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get book
    cur.execute("SELECT * FROM books WHERE bid = %s", [bid])
    book = cur.fetchone()
    return render_template('book.html', book=book)

#register
@app.route('/register/', methods=["GET", "POST"])
def register():
   if request.method =="POST":
            if not request.form.get("username"):
                return flash("must provide username")
            elif not request.form.get("email"):
                return flash("must provide email")    
            elif not request.form.get("password"):
                return flash("must provide password")
            elif not request.form.get("confirm"):
                return flash("must provide password confirmation")
            elif not request.form.get("city"):
                return flash ("must provide a city")
            elif not request.form.get("address"):
                return flash ("please enter your address")        
            elif request.form.get("confirm")!=request.form.get("password"):
                return flash("password and cofirmation aren't the same")
            password= request.form.get("password")
            _password = password = sha256_crypt.hash(password)
            email= request.form.get("email")
            username=request.form.get("username") 
            city = request.form.get("city")
            address = request.form.get("address")             
            c = mysql.connection.cursor()  
            x = c.execute("SELECT * FROM users WHERE username = (%s)",(username,))
            if int(x) > 0:
                flash("That username is already taken, please choose another")
                return render_template('register.html')
            else:
                c.execute("INSERT INTO users (username, password,email,city, address) VALUES (%s, %s, %s, %s, %s)",
                            (username, _password, email, city, address))
                mysql.connection.commit()
                flash("Thanks for registering!")
                c.close()               
                session['logged_in'] = True
                session['username'] = username
                return redirect('/')
   return render_template("register.html")

#login         
@app.route('/login/', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        if not request.form.get("username"):
            return flash("must provide username")
        if not request.form.get("password"):
            return flash("must provide password")    
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']
        # Create cursor
        cur = mysql.connection.cursor()
        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = (%s)", [username])
        if result > 0:
            # Get stored hash
            password = cur.fetchone()['password']
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                if username == 'admin':
                    session['logged_in'] = True
                    session['username'] = username
                    flash('Hello admin')
                    return redirect(url_for('dashboard')) 
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('books'))                
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')
   
# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get articles
    result = cur.execute("SELECT * FROM books")
    if result > 0:
        books = cur.fetchall()
        return render_template('dashboard.html', books=books)
        # Close connection
        cur.close()    
    else:
        msg = 'No books Found'
    return render_template('dashboard.html', msg=msg)

		
# donate
@app.route('/donate', methods=['GET', 'POST'])
@login_required
def donate():    
    if request.method == 'POST': 
        if not request.form.get("booktitle"):
            return flash("must provide book title")
        elif not request.form.get("author"):
            return flash("must provide author")
        elif not request.form.get("price"):
            return flash("must provide price")        
        booktitle = request.form['booktitle']
        author = request.form['author']
        price = request.form['price']
        review = request.form['review']
        original = request.form.get("original")            
        # Create Cursor
        cur = mysql.connection.cursor()
        # Execute
        cur.execute("INSERT INTO books(username, title, author, price, review,original) VALUES(%s, %s, %s, %s, %s, %s)",(session['username'], booktitle, author, price, review, original))
        # Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()
        flash('thank you for your time', 'success')
        return redirect(url_for('books'))
    return render_template('donate.html')            

# Edit book
@app.route('/edit_book/<string:bid>', methods=['GET', 'POST'])
@login_required
def edit_book(bid):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get book by id
    cur.execute("SELECT * FROM books WHERE bid = %s", [bid])
    book = cur.fetchone()
    cur.close()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        original = request.form.get("original")
        price = request.form['price']
        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, author=%s, original=%s, price=%s WHERE bid=%s",(title, author,original, price, bid))
        # Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()
        flash('book Updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_book.html', book=book)


# Delete book
@app.route('/delete_book/<string:bid>', methods=['POST'])
@login_required
def delete_book(bid):
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute
    cur.execute("DELETE FROM books WHERE bid = %s", [bid])
    # Commit to DB
    mysql.connection.commit()
    #Close connection
    cur.close()
    flash('book Deleted')
    return redirect(url_for('dashboard'))

@app.route('/buy_book/<string:bid>', methods=["GET", "POST"])
@login_required
def buy_book(bid):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get book by id
    cur.execute("SELECT * FROM books WHERE bid = %s", [bid])
    book = cur.fetchone()
    cur.close()
    if request.method=="POST":
        cur = mysql.connection.cursor()
        # Execute
        cur.execute("DELETE FROM books WHERE bid = %s", [bid])
        
        # Commit to DB
        mysql.connection.commit()
        #Close connection
        cur.close()               
        flash('this book yours')
        flash('we will contact you soon for shipping info')

        return redirect(url_for('books'))
    return render_template("buy_book.html", book=book)    

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080)

