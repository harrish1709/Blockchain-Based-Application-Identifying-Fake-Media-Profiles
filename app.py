from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from web3 import Web3
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to Ganache Ethereum node or any other Ethereum node
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))

# ABI and Contract Address
abi = [
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"internalType": "uint256",
				"name": "userId",
				"type": "uint256"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "prediction",
				"type": "uint256"
			},
			{
				"indexed": False,
				"internalType": "uint256",
				"name": "blockNumber",
				"type": "uint256"
			}
		],
		"name": "PredictionStored",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "userId",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "prediction",
				"type": "uint256"
			}
		],
		"name": "storePrediction",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "userId",
				"type": "uint256"
			}
		],
		"name": "getPrediction",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	}
]

contract_address = "0x17209273412fa5fE06609Dc35d6B40434825A41A"

# Create contract instance
contract = w3.eth.contract(address=contract_address, abi=abi)

# Load the trained model
model = joblib.load('trained_model.pkl')

# Load the scaler
scalar = joblib.load('scaler.pkl')

def view_prediction(username_to_view, usernames):
    # Find the user ID corresponding to the username
    user_id = usernames.index(username_to_view) + 1

    # Call the getPrediction function to retrieve the prediction and block number
    try:
        prediction, block_number = contract.functions.getPrediction(user_id).call()

        # Retrieve specific block details from Ganache using web3
        block = w3.eth.get_block(block_number)
        transaction_hash = block.transactions[0] if block.transactions else None
        transaction = w3.eth.get_transaction(transaction_hash) if transaction_hash else None
        from_address = transaction['from'] if transaction else None
        to_address = transaction['to'] if transaction else None
        to_contract_address = to_address if contract_address.lower() == to_address.lower() else None

        if prediction == 0:
            return "Username", username_to_view, "is predicted as Genuine.", "Block number:", block.number, "Block hash:", block.hash.hex(), "Gas limit:", block['gasLimit'], "Mined on:", datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S'), "Transaction hash:", transaction_hash, "From address:", from_address, "To contract address:", to_contract_address
        elif prediction == 1:
            return "Username", username_to_view, "is predicted as Fake.", "Block number:", block.number, "Block hash:", block.hash.hex(), "Gas limit:", block['gasLimit'], "Mined on:", datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S'), "Transaction hash:", transaction_hash, "From address:", from_address, "To contract address:", to_contract_address
        else:
            return "Invalid prediction value returned from smart contract."
    
    except Exception as e:
        print("Error:", e)

def read_usernames():
    genuine_users = pd.read_excel("real.xlsx")
    fake_users = pd.read_csv("fake.csv")
    return list(genuine_users['screen_name']) + list(fake_users['screen_name'])

def fetch_prediction_blocks(contract_address):
    prediction_blocks = []
    try:
        # Get the latest block number
        latest_block = w3.eth.block_number
        print("Latest block number:", latest_block)

        # Iterate through blocks to fetch prediction events
        for block_number in range(1, latest_block + 1):
            block = w3.eth.get_block(block_number)
            print("Processing block:", block_number)
            for tx_hash in block.transactions:
                tx = w3.eth.get_transaction(tx_hash)
                try:
                    receipt = w3.eth.get_transaction_receipt(tx_hash)
                    if receipt:
                        # Check if the transaction is to the contract address
                        if receipt.to and receipt.to.lower() == contract_address.lower():
                            # Process the receipt logs to extract prediction event data
                            for log in receipt.logs:
                                if log.address.lower() == contract_address.lower():
                                    topics = log['topics']
                                    if topics[0].hex() == '0xa262c08b3eddff87f9b810553fb6555553d10a0597e95a5f22348cd5763bdc7d':  # Event signature
                                        user_id = int(topics[1].hex(), 16)
                                        prediction_hex = log['data'].hex()
                                        try:
                                            prediction_blocks.append({
                                                'username': user_id,
                                                'block_number': block.number,
                                                'block_hash': block.hash.hex()
                                            })
                                        except ValueError:
                                            print("Error: Invalid prediction data format:", prediction_hex)
                except Exception as e:
                    print("Error processing transaction receipt:", e)
    except Exception as e:
        print("Error fetching prediction blocks:", e)

    return prediction_blocks

# Function to create a connection to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route for the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # Assuming there's an input field for role selection

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the username already exists in the database
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            error = 'Username already exists. Please choose a different username.'
            return render_template('signup.html', error=error)

        # Insert the new user into the database
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('signup.html')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the user exists in the database
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()

        if user:
            # Store user information in the session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']

            conn.close()

            # Redirect to the appropriate page based on the user role
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            error = 'Invalid credentials. Please try again.'
            return render_template('login.html', error=error)

    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' in session and session['role'] == 'admin':
        try:
            # Assuming you have a function to fetch prediction blocks data
            prediction_blocks = fetch_prediction_blocks(contract_address)  # This function should return the prediction blocks data
            return render_template('admin_dashboard.html', username=session['username'], prediction_blocks=prediction_blocks)
        except Exception as e:
            return f"Error: {e}"
    else:
        return redirect(url_for('login'))
    
# Route for the user dashboard
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' in session and session['role'] == 'user':
        return render_template('dynamic.html')
    else:
        return redirect(url_for('login'))

@app.route('/submit_section', methods=['POST'])
def submit_section():
    section = request.form['input1']
    print(section)
    result = view_prediction(section, read_usernames())
    return render_template('dynamic.html',result=result)
@app.route('/submit', methods=['POST'])
def submit():
    followers = float(request.form['Followers'])
    followings = float(request.form['Followings'])
    bio_length = float(request.form['Bio length'])
    private = 1 if request.form.get('checkbox1') == 'on' else 0
    fullname = 1 if request.form.get('checkbox2') == 'on' else 0
    post_count = float(request.form['Post count'])
    avg_media_likes = float(request.form['Average number of media likes'])
    media_count = float(request.form['Media count'])
    last_month_media_count = float(request.form['Last month media count'])
    consecutive_chars_in_username = float(request.form['Consecutive characters in username'])
    num_digits_in_username = float(request.form['Number of digits in username'])

    # Make prediction
    user_input = [[followers, followings, bio_length, private, fullname, post_count, avg_media_likes,
                    media_count, last_month_media_count, consecutive_chars_in_username, num_digits_in_username]]
    user_input_scaled = scalar.transform(user_input)

    # Predict using the loaded model
    prediction = model.predict(user_input_scaled)

    # Analyze the input attributes to provide a reason for the prediction
    reason = "Reason: "
    if prediction[0] == 0:  # Genuine prediction
        if followers >= 1000:
            reason += "High number of followers. "
        if followings <= 500:
            reason += "Low number of followings. "
        if bio_length >= 50:
            reason += "Long bio length. "
        if post_count >= 50:
            reason += "High number of posts. "
        if avg_media_likes >= 10:
            reason += "High average media likes. "
        if not private:
            reason += "Account is not private. "
        if num_digits_in_username <= 2:
            reason += "Low number of digits in username. "
        if last_month_media_count >= 10:
            reason += "High last month media count. "
        if fullname:
            reason += "Account has a full name. "
        if consecutive_chars_in_username < 3:
            reason += "Low consecutive characters in username. "

    elif prediction[0] == 1:  # Fake prediction
        if followers < 1000:
            reason += "Low number of followers. "
        if followings > 500:
            reason += "High number of followings. "
        if bio_length < 50:
            reason += "Short bio length. "
        if post_count < 50:
            reason += "Low number of posts. "
        if avg_media_likes < 10:
            reason += "Low average media likes. "
        if private:
            reason += "Account is private. "
        if num_digits_in_username > 2:
            reason += "High number of digits in username. "
        if last_month_media_count < 10:
            reason += "Low last month media count. "
        if not fullname:
            reason += "No full name. "
        if consecutive_chars_in_username >= 3:
            reason += "High consecutive characters in username. "
        
    else:
        reason += "Invalid prediction."

    if prediction[0] == 0:
        result = "Predicted as Genuine."
    elif prediction[0] == 1:
        result = "Predicted as Fake."
    else:
        result = "Invalid prediction."

    # Include the reason in the result
    result += "\n" + reason

    return render_template('dynamic.html', result=result)

# Route for logging out
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)