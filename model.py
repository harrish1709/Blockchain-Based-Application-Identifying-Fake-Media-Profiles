from web3 import Web3  
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib

# Connect to Ganache Ethereum node or any other Ethereum node
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))

# ABI and Contract Address (Assuming it's the same as before)
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


def store_prediction(user_id, prediction):
    user_id_uint = int(user_id)
    prediction_uint = int(prediction)

    # Specify the 'from' address
    from_address = "0x0D0E731efbF9C34574b7f1c7b212eD5115EF1407"

    # Store prediction in the blockchain
    tx_hash = contract.functions.storePrediction(user_id_uint, prediction_uint).transact({'from': from_address})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Prediction stored in the blockchain for user ID:", user_id)


def read_and_preprocess_dataset():
    genuine_users = pd.read_excel("real.xlsx")
    fake_users = pd.read_csv("fake.csv")
    
    # Check if the datasets are loaded correctly
    print("Number of rows in genuine_users dataset:", genuine_users.shape[0])
    print("Number of rows in fake_users dataset:", fake_users.shape[0])

    # Concatenate the datasets
    dataset = pd.concat([genuine_users, fake_users], ignore_index=True)

    # Check if concatenation is done correctly
    print("Number of rows after concatenation:", dataset.shape[0])

    # Select only the specified feature columns
    feature_columns_to_use = ['Followers', 'Followings', 'Bio length', 'Fullname', 'Private',
                              'Post count', 'Average number of media likes', 'Media count',
                              'Last month media count', 'Consecutive characters in username',
                              'Number of digits in username']
    X = dataset[feature_columns_to_use]

    # Handle missing values
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)
    X = pd.DataFrame(X_imputed, columns=feature_columns_to_use)  # Provide feature names

    # Preprocessing
    scalar = StandardScaler()
    X_scaled = scalar.fit_transform(X)

    # Save the scaler
    joblib.dump(scalar, 'scaler.pkl')

    # Extracting labels
    y = [0] * len(genuine_users) + [1] * len(fake_users)

    return X_scaled, y


def preprocess_and_predict(X, y):
    # Train a Random Forest Classifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)

    return clf


def main1():
    # Read and preprocess dataset
    X, y = read_and_preprocess_dataset()

    # Train the model
    model = preprocess_and_predict(X, y)

    # Make predictions
    predictions = model.predict(X)
    joblib.dump(model, 'trained_model.pkl')
    # Store predictions for each user ID
    for user_id, prediction in enumerate(predictions, start=1):
        store_prediction(user_id, prediction)

if __name__ == '__main__':
    main1()
