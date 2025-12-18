from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
import os


try:
    install_solc('0.8.0')
    set_solc_version('0.8.0')
except:
    pass


GANACHE_URL = os.environ.get('GANACHE_URL', 'http://127.0.0.1:8545')
web3 = Web3(Web3.HTTPProvider(GANACHE_URL))


CONTRACT_PATH = os.path.join(os.path.dirname(__file__), 'PaymentContract.sol')


def get_compiled_contract():
    with open(CONTRACT_PATH, 'r') as file:
        contract_source = file.read()

    compiled = compile_source(
        contract_source,
        output_values=['abi', 'bin']
    )

    contract_id, contract_interface = compiled.popitem()
    return contract_interface


def deploy_contract(owner_address, customer_address, amount_in_wei, owner_private_key):

    contract_interface = get_compiled_contract()

    Contract = web3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )

    construct_txn = Contract.constructor(
        owner_address,
        customer_address,
        amount_in_wei
    ).build_transaction({
        'from': owner_address,
        'nonce': web3.eth.get_transaction_count(owner_address),
        'gas': 3000000,
        'gasPrice': 1
    })

    signed = web3.eth.account.sign_transaction(construct_txn, owner_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_receipt.contractAddress


def get_contract_instance(contract_address):
    contract_interface = get_compiled_contract()
    return web3.eth.contract(
        address=contract_address,
        abi=contract_interface['abi']
    )


def check_payment_status(contract_address):
    contract = get_contract_instance(contract_address)
    return contract.functions.isPaid().call()


def assign_courier_to_contract(contract_address, courier_address, owner_private_key):
    contract = get_contract_instance(contract_address)
    owner_address = web3.eth.account.from_key(owner_private_key).address

    txn = contract.functions.assignCourier(courier_address).build_transaction({
        'from': owner_address,
        'nonce': web3.eth.get_transaction_count(owner_address),
        'gas': 200000,
        'gasPrice': 1
    })

    signed = web3.eth.account.sign_transaction(txn, owner_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)


def finalize_contract(contract_address, owner_private_key):
    contract = get_contract_instance(contract_address)
    owner_address = web3.eth.account.from_key(owner_private_key).address

    txn = contract.functions.finalize().build_transaction({
        'from': owner_address,
        'nonce': web3.eth.get_transaction_count(owner_address),
        'gas': 200000,
        'gasPrice': 1
    })

    signed = web3.eth.account.sign_transaction(txn, owner_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)


def generate_payment_transaction(contract_address, customer_address, amount_in_wei):

    contract = get_contract_instance(contract_address)

    txn = contract.functions.pay().build_transaction({
        'from': customer_address,
        'value': amount_in_wei,
        'nonce': web3.eth.get_transaction_count(customer_address),
        'gas': 200000,
        'gasPrice': 1
    })

    return txn