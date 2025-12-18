from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


product_categories = database.Table('product_categories',
                                    database.Column('product_id', database.Integer, database.ForeignKey('products.id'),
                                                    primary_key=True),
                                    database.Column('category_id', database.Integer,
                                                    database.ForeignKey('categories.id'), primary_key=True)
                                    )



class OrderItem(database.Model):
    __tablename__ = 'order_items'

    id = database.Column(database.Integer, primary_key=True)
    order_id = database.Column(database.Integer, database.ForeignKey('orders.id'), nullable=False)
    product_id = database.Column(database.Integer, database.ForeignKey('products.id'), nullable=False)
    quantity = database.Column(database.Integer, nullable=False)
    price = database.Column(database.Float, nullable=False)

    product = database.relationship('Product', back_populates='order_items')


class Product(database.Model):
    __tablename__ = 'products'

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)
    price = database.Column(database.Float, nullable=False)

    categories = database.relationship('Category', secondary=product_categories, back_populates='products')
    order_items = database.relationship('OrderItem', back_populates='product')

    def __repr__(self):
        return f"Product({self.id}, {self.name}, {self.price})"


class Category(database.Model):
    __tablename__ = 'categories'

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False, unique=True)

    products = database.relationship('Product', secondary=product_categories, back_populates='categories')

    def __repr__(self):
        return f"Category({self.id}, {self.name})"


class Order(database.Model):
    __tablename__ = 'orders'

    id = database.Column(database.Integer, primary_key=True)
    customer_email = database.Column(database.String(256), nullable=False)
    price = database.Column(database.Float, nullable=False)
    status = database.Column(database.String(50), nullable=False, default='CREATED')  # CREATED, PENDING, COMPLETE
    timestamp = database.Column(database.DateTime, nullable=False)

    contract_address = database.Column(database.String(42), nullable=True)

    items = database.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f"Order({self.id}, {self.customer_email}, {self.status})"