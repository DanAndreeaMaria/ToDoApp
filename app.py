import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from datetime import datetime, timedelta, timezone

# Configure application
app = Flask(__name__)
app.secret_key = 'your_secret_key' # Required for session

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Helper function to get data from the database
def get_user_tasks(user_id):
  """Fetch all tasks belonging to the given user"""
  conn = sqlite3.connect('todo_database.db') # opens a connection to the SQLite database file todo_database.db
  conn.execute("PRAGMA foreign_keys = ON")
  conn.row_factory = sqlite3.Row # allows dict-like access
  cursor = conn.cursor() # creates a cursor object to execute SQL queries

  cursor.execute("SELECT id, task, completed FROM user_tasks WHERE user_id = ? ORDER BY id DESC", (user_id,))
  rows = cursor.fetchall()

  conn.close()
  return rows

# Helper function to interact with users table
def query_db(query, args=(), one=False, commit=False):
  conn = sqlite3.connect('todo_database.db')
  conn.row_factory = sqlite3.Row
  cursor = conn.cursor()
  cursor.execute(query, args)
  if commit:
    conn.commit()
    result = cursor.lastrowid if query.strip().upper().startswith("INSERT") else None # For INSERTs
  else:
    result = cursor.fetchall()
  conn.close()
  return result if not one else (result[0] if result else None)

@app.after_request
def after_request(response):
  """Ensure responses aren't cached"""
  response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
  response.headers["Expires"] = 0
  response.headers["Pragma"] = "no-cache"
  return response

@app.route("/")
def index():
  if "user_id" not in session:
    return redirect("/login")
  
  tasks = get_user_tasks(session["user_id"])
  return render_template('index.html', tasks=tasks) # Tells Flask to load templates/index.html and pass the data into the HTML as a variable

@app.route("/login", methods=["GET", "POST"])
def login():
  """Log user in"""

  # Forget any user_id
  session.clear()

  # User reached route via POST (as by submitting a form via POST)
  if request.method == "POST":
    # Ensure username was submitted
    if not request.form.get("username"):
      session["error"] = "Must provide username"
    
    # Ensure the password was submitted
    elif not request.form.get("password"):
      session["error"] = "Must provide password"
    
    # Query database for username
    rows = query_db("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))

    # Ensure username exists and password is correct
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
      session["error"] = "Invalid username/password"
    
    # Remember which user has logged in
    session["user_id"] = rows[0]["id"]
    session["username"] = rows[0]["username"]

    # Redirect user to homepage
    return redirect("/")
  
  # User reached route via GET (as by clicking a link or via redirect)
  else:
    return render_template("login.html")
  
@app.route("/logout")
def logout():
  """Log user out"""
  # Forget any user_id
  session.clear()
  # Redirect user to login form
  return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
  """Register user"""
  if request.method == "POST":
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    # Check for possible errors
    if not username:
      session["error"] = "Must provide username"
      return redirect("/register")
    if not password:
      session["error"] = "Must provide password"
      return redirect("/register")
    if not confirmation:
      session["error"] = "Must confirm password"
      return redirect("/register")
    if password != confirmation:
      session["error"] = "Passwords do not match"
      return redirect("/register")
    
    existing_user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
    # Check if username already exists
    if existing_user:
      session["error"] = "Username already exists"
      return redirect("/register")
    
    # Hash the password
    hashed_password = generate_password_hash(password)
    # Insert the new user into the db and get their new user id
    new_user_id = query_db("INSERT INTO users (username, hash) VALUES (?, ?)", (username, hashed_password), commit=True)

    # Log the user by storing their id in session
    session["user_id"] = new_user_id

    # Add success message after registering
    session["success"] = "Account created successfully! You can now log in!"
    return redirect("/login")
  
  # Handle GET: display error if set, then clear it
  error = session.pop("error", None)
  return render_template("register.html", error=error)

@app.route("/todo")
def todo():
  # Pass it into the template
  return render_template("todo.html")

@app.route("/add_task", methods=["POST"])
def add_task():
  """Add a new task for the logged-in user"""
  if "user_id" not in session:
    return redirect("/login")
  
  task_text = request.form.get("task")

  # In case the user has no input
  if not task_text.strip():
    session["error"] = "Task cannot be empty"
    return redirect("/")
  
  # Insert the task into the database
  query_db(
    "INSERT INTO user_tasks (user_id, task) VALUES (?, ?)",
  (session["user_id"], task_text),
  commit=True
  )

  return redirect("/")

# Mark task complete/incomplete
@app.route("/toggle_task/<int:task_id>", methods=["POST"])
def toggle_task(task_id):
  if "user_id" not in session:
    return redirect("/login")
  
  # Flip completed status (from 0 -> 1 or from 1 -> 0)
  query_db(
    """
    UPDATE user_tasks
    SET completed = CASE completed WHEN 0 THEN 1 ELSE 0 END 
    WHERE id = ? AND user_id = ?  
    """,
    (task_id, session["user_id"]),
    commit=True
  )
  return redirect("/")

# Delete task - on user_tasks table, the field 'completed' is 0 for 'not completed' and 1 for 'completed'
@app.route("/delete_task/<int:task_id>", methods=["POST"])
def delete_task(task_id):
  if "user_id" not in session:
    return redirect("/login")
  
  query_db("DELETE FROM user_tasks WHERE id = ? AND user_id = ?", (task_id, session["user_id"]), commit=True)
  return redirect("/")
  
# Run the app
if __name__=='__main__':
  app.run(debug=True)




