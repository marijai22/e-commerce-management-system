from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt, verify_jwt_in_request
from configuration import Configuration
from models import database, Product, Category, Order, OrderItem
from datetime import datetime
from functools import wraps
from sqlalchemy import and_
import os


from web3 import Web3

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)
jwt = JWTManager(application)


def role_required(role):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("roles") != role:
                return jsonify({"msg": "Missing Authorization Header"}), 401
            return function(*args, **kwargs)

        return wrapper

    return decorator


@application.route("/search", methods=["GET"])
@role_required("customer")
def search():
    product_name = request.args.get('name', '')
    category_name = request.args.get('category', '')

    query = Product.query

    if category_name:
        query = query.join(Product.categories).filter(Category.name.like(f'%{category_name}%'))

    if product_name:
        query = query.filter(Product.name.like(f'%{product_name}%'))

    products = query.all()

    categories_set = set()
    products_list = []

    for product in products:
        categories = [cat.name for cat in product.categories]
        categories_set.update(categories)

        products_list.append({
            "categories": categories,
            "id": product.id,
            "name": product.name,
            "price": product.price
        })

    return jsonify({
        "categories": sorted(list(categories_set)),
        "products": products_list
    }), 200


@application.route("/order", methods=["POST"])
@role_required("customer")
def order():
    claims = get_jwt()
    customer_email = claims.get("sub")

    data = request.get_json()

    if 'requests' not in data:
        return jsonify({"message": "Field requests is missing."}), 400

    requests_list = data['requests']

    #provera svih prozivoda iz requests
    for index, req in enumerate(requests_list):
        if 'id' not in req:
            return jsonify({"message": f"Product id is missing for request number {index}."}), 400

        if 'quantity' not in req:
            return jsonify({"message": f"Product quantity is missing for request number {index}."}), 400

        try:
            product_id = int(req['id'])
            if product_id <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"message": f"Invalid product id for request number {index}."}), 400

        try:
            quantity = int(req['quantity'])
            if quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"message": f"Invalid product quantity for request number {index}."}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"message": f"Invalid product for request number {index}."}), 400

    # uvek treba proveriti blockchain validaciju
    if 'address' not in data:
        return jsonify({"message": "Field address is missing."}), 400

    address = data.get('address', '').strip()
    if not address or address == "":
        return jsonify({"message": "Field address is missing."}), 400


    if not Web3.is_address(address):
        return jsonify({"message": "Invalid address."}), 400

    # pravimo narudzbinu
    total_price = 0
    order_items = []

    for req in requests_list:
        product = Product.query.get(req['id'])
        quantity = req['quantity']
        item_price = product.price * quantity
        total_price += item_price

        order_item = OrderItem(
            product_id=product.id,
            quantity=quantity,
            price=product.price
        )
        order_items.append(order_item)

    new_order = Order(
        customer_email=customer_email,
        price=total_price,
        status='CREATED',
        timestamp=datetime.utcnow()
    )

    for item in order_items:
        new_order.items.append(item)

    database.session.add(new_order)
    database.session.commit()

    try:
        from contracts.contract_manager import deploy_contract

        # owner private key
        owner_private_key = os.environ.get('OWNER_PRIVATE_KEY',
                                           '0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d')

        # owner address
        owner_account = Web3().eth.account.from_key(owner_private_key)
        owner_address = owner_account.address

        amount_in_wei = int(new_order.price * 100)


        contract_address = deploy_contract(
            owner_address=owner_address,
            customer_address=address,
            amount_in_wei=amount_in_wei,
            owner_private_key=owner_private_key
        )

        # cuvamo contract address
        new_order.contract_address = contract_address
        database.session.commit()

    except Exception as e:
        print(f"Blockchain error in /order: {str(e)}")
        database.session.rollback()
        return jsonify({"message": f"Blockchain error: {str(e)}"}), 500

    return jsonify({"id": new_order.id}), 200


@application.route("/status", methods=["GET"])
@role_required("customer")
def status():
    try:
        claims = get_jwt()
        customer_email = claims.get("sub")

        orders = Order.query.filter(Order.customer_email == customer_email).all()

        if not orders:
            return jsonify({"orders": []}), 200

        orders_list = []
        for order in orders:
            products_list = []
            for item in order.items:
                product = item.product
                products_list.append({
                    "categories": [cat.name for cat in product.categories],
                    "name": product.name,
                    "price": float(item.price),
                    "quantity": item.quantity
                })

            orders_list.append({
                "products": products_list,
                "price": float(order.price),
                "status": order.status,
                "timestamp": order.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
            })

        return jsonify({"orders": orders_list}), 200

    except Exception as e:
        print(f"ERROR in /status: {str(e)}")
        return jsonify({"message": str(e)}), 500


@application.route("/delivered", methods=["POST"])
@role_required("customer")
def delivered():
    try:
        claims = get_jwt()
        customer_email = claims.get("sub")

        data = request.get_json()


        if 'id' not in data:
            return jsonify({"message": "Missing order id."}), 400

        try:
            order_id = int(data['id'])
            if order_id <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"message": "Invalid order id."}), 400


        order = Order.query.get(order_id)

        if not order or order.customer_email != customer_email:
            return jsonify({"message": "Invalid order id."}), 400

        # order mora da bude u statusu PENDING
        if order.status != 'PENDING':
            return jsonify({"message": "Delivery not complete."}), 400

        # finalizacija blockchaina
        if order.contract_address:
            try:
                from contracts.contract_manager import finalize_contract

                owner_private_key = os.environ.get('OWNER_PRIVATE_KEY',
                                                   '0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d')

                # finalizujemo contract - distribuiramo sredstva
                finalize_contract(order.contract_address, owner_private_key)

            except Exception as e:
                print(f"Blockchain error in /delivered: {str(e)}")
                return jsonify({"message": f"Blockchain error: {str(e)}"}), 500

        # menjamo status u COMPLETE
        order.status = 'COMPLETE'
        database.session.commit()

        return "", 200

    except Exception as e:
        print(f"ERROR in /delivered: {str(e)}")
        return jsonify({"message": str(e)}), 500


@application.route("/generate_invoice", methods=["POST"])
@role_required("customer")
def generate_invoice():
    try:
        claims = get_jwt()
        customer_email = claims.get("sub")
        data = request.get_json()

        if 'id' not in data:
            return jsonify({"message": "Missing order id."}), 400

        try:
            order_id = int(data['id'])
            if order_id <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({"message": "Invalid order id."}), 400

        order = Order.query.get(order_id)
        if not order or order.customer_email != customer_email:
            return jsonify({"message": "Invalid order id."}), 400

        if 'address' not in data:
            return jsonify({"message": "Missing address."}), 400

        address = data.get('address', '').strip()

        # prazan string je INVALID
        if address == "":
            return jsonify({"message": "Invalid address."}), 400

        if not Web3.is_address(address):
            return jsonify({"message": "Invalid address."}), 400

        if not order.contract_address:
            return jsonify({"message": "Invalid order id."}), 400

        # da li je vec placeno
        try:
            from contracts.contract_manager import check_payment_status

            is_paid = check_payment_status(order.contract_address)
            if is_paid:
                return jsonify({"message": "Transfer already complete."}), 400
        except Exception as e:
            print(f"Error checking payment: {str(e)}")

        # generisemo payment transakciju
        from contracts.contract_manager import generate_payment_transaction

        amount_in_wei = int(order.price * 100)

        transaction = generate_payment_transaction(
            contract_address=order.contract_address,
            customer_address=address,
            amount_in_wei=amount_in_wei
        )

        return jsonify({"invoice": transaction}), 200

    except Exception as e:
        print(f"ERROR in /generate_invoice: {str(e)}")
        return jsonify({"message": f"Error: {str(e)}"}), 500


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5002)