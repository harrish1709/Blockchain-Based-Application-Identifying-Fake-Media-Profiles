from web3 import Web3
import json

# Load the ABI of your contract
with open('contract.json', 'r') as f:
    contract_data = f.read()

# Parse the JSON data
try:
    contract_abi = json.loads(contract_data)
except json.JSONDecodeError as e:
    print("Error loading contract ABI:", e)
    contract_abi = None

# Check if ABI was loaded successfully
if contract_abi:
    print("Type of contract_abi:", type(contract_abi))
    print("Contract ABI:", contract_abi)

    # Find the ABI entry for the PredictionStored event
    event_abi = next((item for item in contract_abi["abi"] if item.get('type') == 'event' and item.get('name') == 'PredictionStored'), None)

    if event_abi:
        # Get the parameter types of the PredictionStored event
        param_types = [param['type'] for param in event_abi['inputs']]

        # Concatenate the event name with the parameter types
        event_signature = f"{event_abi['name']}({','.join(param_types)})"

        # Hash the event signature using Keccak-256
        event_hash = Web3.keccak(text=event_signature).hex()

        print("Event signature:", event_hash)
    else:
        print("Event 'PredictionStored' not found in the contract ABI.")
else:
    print("Failed to load contract ABI.")
