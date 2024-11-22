import json
from flask import Flask, render_template, request, redirect, url_for, flash
import re
import random
from datetime import datetime

main = Flask(__name__)
main.secret_key = 'your_secret_key' 

DATA_FILE = 'accounts_data.json'


def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"accounts": {}, "transactions": {}}  

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Load data on app startup
data = load_data()
accounts = data['accounts']
transactions = data['transactions']


@main.route('/')
def welcome():
    return render_template('welcome.html')

# Route for creating an account
@main.route('/create_account', methods=['POST', 'GET'])
def create_account():
    if request.method == 'POST':
      
        name = request.form['name']
        surname = request.form['surname']
        phone = request.form['phone']
        id_number = request.form['id_number']
        username = request.form['username']
        password = request.form['password']  

        
        errors = []

    
        if not re.match("^[a-zA-Z]+$", name): 
            errors.append("First Name can only contain letters.")

        if not re.match("^[a-zA-Z]+$", surname): 
            errors.append("Last Name can only contain letters.")
            
        if not re.match("^\d{10}$", phone):  
            errors.append("Phone number must be exactly 10 digits.")

        if not re.match("^\d{13}$", id_number):  
            errors.append("ID Number must be exactly 13 digits.")

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", username):  
            errors.append("Username must be a valid email address.")

        # Check if ID number already exists in the system
        for account_data in accounts.values():
            if account_data['id_number'] == id_number:
                errors.append("This ID number already exists in the system. Please use a different ID.")

   
        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for('create_account'))

    
        account_number = ''.join([str(random.randint(0, 9)) for _ in range(12)])

        while account_number in accounts:
            account_number = ''.join([str(random.randint(0, 9)) for _ in range(12)])

        # Create the account
        accounts[account_number] = {
            'name': name,
            'surname': surname,
            'phone': phone,
            'id_number': id_number,
            'username': username,
            'password': password,
            'balance': 0,
            'transactions': []
        }

     
        flash(f"Account successfully created! Your account number is {account_number}.", "success")
        save_data({"accounts": accounts, "transactions": transactions}) 
        return redirect(url_for('login'))  
    return render_template('index.html')  

# Route for login
@main.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

      
        print(f"Login attempt: username={username}, password={password}")
        print(f"Accounts: {accounts}")

       
        for account_number, account_data in accounts.items():
            if account_data['username'] == username and account_data['password'] == password:
                print(f"Login successful for account: {account_number}")
                return redirect(url_for('dashboard', account_number=account_number))  

        print("Login failed: Invalid username or password")
        flash("Invalid username or password, please try again.", "error")
        return redirect(url_for('login'))

    return render_template('login.html')

@main.route('/dashboard/<account_number>', methods=['POST', 'GET'])
def dashboard(account_number):
    account = accounts.get(account_number)
    if not account:
        flash("Invalid account. Please log in again.", "error")
        return redirect(url_for('login'))

 
    if request.method == 'POST':
        action = request.form['action']
        amount = float(request.form['amount'])

     
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Deposit funds
        if action == 'deposit':
            account['balance'] += amount
            transaction = {
                'date': timestamp,
                'type': 'Deposit',
                'amount': amount,
                'details': f"Deposited R{amount}"
            }
            account['transactions'].append(transaction)
            flash(f"Successfully deposited R{amount}.", "success")


        # Withdraw funds
        elif action == 'withdraw':
            if account['balance'] >= amount:
                account['balance'] -= amount
                transaction = {
                    'date': timestamp,
                    'type': 'Withdraw',
                    'amount': amount,
                    'details': f"Withdrew R{amount}"
                }
                account['transactions'].append(transaction)
                flash(f"Successfully withdrew R{amount}.", "success")
            else:
                flash("Insufficient funds.", "error")

        # Transfer funds
        elif action == 'transfer':
            recipient_account_number = request.form['recipient_account']
            recipient_account = accounts.get(recipient_account_number)
            if recipient_account and account['balance'] >= amount:
                account['balance'] -= amount
                recipient_account['balance'] += amount
                transaction = {
                    'date': timestamp,
                    'type': 'Transfer',
                    'amount': amount,
                    'details': f"Transferred R{amount} to Account {recipient_account_number}"
                }
                account['transactions'].append(transaction)
                recipient_transaction = {
                    'date': timestamp,
                    'type': 'Received',
                    'amount': amount,
                    'details': f"Received R{amount} from Account {account_number}"
                }
                recipient_account['transactions'].append(recipient_transaction)
                flash(f"Successfully transferred R{amount} to account {recipient_account_number}.", "success")
            else:
                flash("Transaction failed. Please check recipient account and balance.", "error")

        save_data({"accounts": accounts, "transactions": transactions})

    return render_template('dashboard.html', account=account, account_number=account_number)

if __name__ == '__main__':
    main.run(debug=True, port=800)
