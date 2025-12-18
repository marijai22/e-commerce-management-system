from flask import Flask
from configuration import Configuration
from models import database, Product, Category, Order, OrderItem

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)


def create_database():
    with application.app_context():
        database.create_all()
        print("Shop database created successfully!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "create_database":
            create_database()
    else:
        create_database()