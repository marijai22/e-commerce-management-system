from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt
from configuration import Configuration
from models import database, Product, Category, product_categories, Order, OrderItem
import io
import csv

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


@application.route("/update", methods=["POST"])
@role_required("owner")
def update():
    if 'file' not in request.files:
        return jsonify({"message": "Field file is missing."}), 400

    file = request.files['file']

    try:
        content = file.read().decode('utf-8-sig')
    except Exception:
        return jsonify({"message": "Field file is missing."}), 400

    csv_reader = csv.reader(io.StringIO(content))

    products_to_add = []
    line_number = 0

    # eventualne greske u CSV-u
    for row in csv_reader:
        if len(row) != 3:
            return jsonify({"message": f"Incorrect number of values on line {line_number}."}), 400

        categories_str, product_name, price_str = row

        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError
        except ValueError:
            return jsonify({"message": f"Incorrect price on line {line_number}."}), 400

        category_names = categories_str.split('|')
        products_to_add.append({
            'name': product_name,
            'price': price,
            'categories': category_names
        })

        line_number += 1

    # provera duplikata
    for product_data in products_to_add:
        existing_product = Product.query.filter(Product.name == product_data['name']).first()
        if existing_product:
            return jsonify({"message": f"Product {product_data['name']} already exists."}), 400

    # dodajemo sve proizvode
    for product_data in products_to_add:
        product = Product(name=product_data['name'], price=product_data['price'])

        for category_name in product_data['categories']:
            category = Category.query.filter(Category.name == category_name).first()

            if not category:
                category = Category(name=category_name)
                database.session.add(category)

            product.categories.append(category)

        database.session.add(product)

    database.session.commit()

    return "", 200


@application.route("/product_statistics", methods=["GET"])
@role_required("owner")
def product_statistics():
    from sqlalchemy import func, case

    statistics = database.session.query(
        Product.name,
        func.coalesce(
            func.sum(
                case(
                    [(Order.status == 'COMPLETE', OrderItem.quantity)],
                    else_=0
                )
            ), 0
        ).label('sold'),
        func.coalesce(
            func.sum(
                case(
                    [(Order.status.in_(['CREATED', 'PENDING']), OrderItem.quantity)],
                    else_=0
                )
            ), 0
        ).label('waiting')
    ).outerjoin(OrderItem, Product.id == OrderItem.product_id) \
        .outerjoin(Order, OrderItem.order_id == Order.id) \
        .group_by(Product.id, Product.name) \
        .all()

    # filtriramo samo proizvode koji imaju sold > 0 ILI waiting > 0
    result = []
    for name, sold, waiting in statistics:
        sold_int = int(sold) if sold else 0
        waiting_int = int(waiting) if waiting else 0

        if sold_int > 0 or waiting_int > 0:
            result.append({
                "name": name,
                "sold": sold_int,
                "waiting": waiting_int
            })

    return jsonify({"statistics": result}), 200


@application.route("/category_statistics", methods=["GET"])
@role_required("owner")
def category_statistics():
    from sqlalchemy import func, desc, asc

    # statistike za kategorije sa prodatim proizvodima
    category_stats = database.session.query(
        Category.name,
        func.coalesce(func.sum(OrderItem.quantity), 0).label('total_sold')
    ).join(product_categories, Category.id == product_categories.c.category_id) \
        .join(Product, Product.id == product_categories.c.product_id) \
        .join(OrderItem, OrderItem.product_id == Product.id) \
        .join(Order, Order.id == OrderItem.order_id) \
        .filter(Order.status == 'COMPLETE') \
        .group_by(Category.id, Category.name) \
        .all()

    category_dict = {name: int(total) for name, total in category_stats}

    # dodajemo sve kategorije koje nemaju prodate proizvode
    all_categories = Category.query.all()
    for category in all_categories:
        if category.name not in category_dict:
            category_dict[category.name] = 0

    # sortiramo po broju prodatih DESC, pa po imenu ASC
    sorted_categories = sorted(
        category_dict.items(),
        key=lambda x: (-x[1], x[0])
    )

    result = [name for name, _ in sorted_categories]

    return jsonify({"statistics": result}), 200


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5001)