from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from configuration import Configuration
from models import database, Order
from web3 import Web3
import os

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)
jwt = JWTManager(application)


def role_required(role):
    def decorator(func):
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("roles") != role:
                return jsonify({"msg": "Missing Authorization Header"}), 401
            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


@application.route("/orders_to_deliver", methods=["GET"])
@role_required("courier")
def orders_to_deliver():
    # uzimamo samo kreirane porudzbine
    orders = Order.query.filter(Order.status == 'CREATED').all()

    orders_list = []
    for order in orders:
        orders_list.append({
            "id": order.id,
            "email": order.customer_email
        })

    return jsonify({"orders": orders_list}), 200


@application.route("/pick_up_order", methods=["POST"])
@role_required("courier")
def pick_up_order():
    data = request.get_json()

    if 'id' not in data:
        return jsonify({"message": "Missing order id."}), 400

    try:
        order_id = int(data['id'])
        if order_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid order id."}), 400

    # moramo da vidimo da li taj order uopste postoji
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"message": "Invalid order id."}), 400

    # da li je porudzbina kreirana
    if order.status != 'CREATED':
        return jsonify({"message": "Invalid order id."}), 400

    # blockchain provera
    if 'address' not in data:
        return jsonify({"message": "Missing address."}), 400

    courier_address = data.get('address', '').strip()
    if courier_address == "":
        return jsonify({"message": "Missing address."}), 400

    # proveravamo da li je Etherum adresa validna
    if not Web3.is_address(courier_address):
        return jsonify({"message": "Invalid address."}), 400

    # da li postoji contract
    if not order.contract_address:
        return jsonify({"message": "Invalid order id."}), 400

    # da li je kupac platio
    try:
        from contracts.contract_manager import check_payment_status, assign_courier_to_contract

        is_paid = check_payment_status(order.contract_address)
        if not is_paid:
            return jsonify({"message": "Transfer not complete."}), 400

        # dodeljujemo kurira contractu
        owner_private_key = os.environ.get('OWNER_PRIVATE_KEY',
                                           '0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d')

        assign_courier_to_contract(order.contract_address, courier_address, owner_private_key)

    except Exception as e:
        print(f"Blockchain error: {str(e)}")
        return jsonify({"message": "Transfer not complete."}), 400

    #menjamo status
    order.status = 'PENDING'
    database.session.commit()

    return "", 200


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5003)