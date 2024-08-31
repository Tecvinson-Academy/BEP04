from flask import Flask, render_template, request, redirect, url_for, session, flash
import mariadb
import sys
from flask_bcrypt import Bcrypt

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'

# Database connection
try:
    conn = mariadb.connect(
        user="root",  # Replace with your MariaDB username
        password="root123#",  # Replace with your MariaDB password
        host="localhost",  # Replace with your MariaDB host if different
        port=3306,  # Replace with your MariaDB port if different
        database="restaurant_reservation_db"  # Replace with your database name
    )
    cursor = conn.cursor()
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

bcrypt = Bcrypt(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and bcrypt.check_password_hash(user[2], password):  # Assuming user[2] is the password column
            session['user_id'] = user[0]  # Store the user ID in the session
            return redirect(url_for('reservations'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if the email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('This email is already registered. Please use a different email or log in.')
            return redirect(url_for('register'))
        
        # Hash The Password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        cursor.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)", 
                       (username, hashed_password, email))
        conn.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/reservations')
def reservations():
    if 'user_id' not in session:
        flash('Please log in to view your reservations.')
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    cursor.execute("SELECT * FROM reservations WHERE user_id = %s", (user_id,))
    reservations = cursor.fetchall()
    
    return render_template('reservations.html', reservations=reservations)

@app.route('/make_reservation', methods=['POST'])
def make_reservation():
    if 'user_id' not in session:
        flash('Please log in to make a reservation.')
        return redirect(url_for('index'))
    
    try:
        user_id = session['user_id']
        reservation_date = request.form['reservation_date']
        reservation_time = request.form['reservation_time']
        table_number = int(request.form['table_number'])
        num_persons = int(request.form['num_persons'])

        # Validate the form inputs
        if not reservation_date or not reservation_time or table_number <= 0 or num_persons <= 0:
            raise ValueError("Invalid reservation details provided.")

        # Insert the reservation into the database
        cursor.execute(
            "INSERT INTO reservations (user_id, reservation_date, reservation_time, table_number, num_persons) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_id, reservation_date, reservation_time, table_number, num_persons)
        )
        conn.commit()
        flash('Reservation made successfully!')
        return redirect(url_for('reservations'))

 
    except ValueError as ve:
        flash(str(ve))
        return redirect(url_for('reservations'))

    except mariadb.Error as e:
        conn.rollback()  # Rollback in case of error
        flash('An error occurred while processing your reservation.')
        print(f"Error: {e}")
        return redirect(url_for('reservations'))

    except Exception as e:
        flash('Something went wrong. Please try again.')
        print(f"Unexpected error: {e}")
        return redirect(url_for('reservations'))

if __name__ == '__main__':
    app.run(debug=True)
