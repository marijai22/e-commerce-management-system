from flask import Flask;
from configuration import Configuration;
from models import database, User;
from passlib.hash import sha256_crypt;

application = Flask(__name__);
application.config.from_object(Configuration);

database.init_app(application);


def create_database():
    with application.app_context():
        database.create_all();
        print("Database created successfully!");


def init_owner():
    with application.app_context():
        existing_owner = User.query.filter(User.email == "onlymoney@gmail.com").first();

        if existing_owner:
            print("Owner already exists!");
            return;

        owner = User(
            email="onlymoney@gmail.com",
            password=sha256_crypt.hash("evenmoremoney"),
            forename="Scrooge",
            surname="McDuck",
            role="owner"
        );

        database.session.add(owner);
        database.session.commit();
        print("Owner created successfully!");


if __name__ == "__main__":
    import sys;

    if len(sys.argv) > 1:
        if sys.argv[1] == "create_database":
            create_database();
        elif sys.argv[1] == "init_owner":
            init_owner();
        elif sys.argv[1] == "init_all":
            create_database();
            init_owner();
    else:
        create_database();