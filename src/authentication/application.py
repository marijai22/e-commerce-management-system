from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from configuration import Configuration
from models import database, User  # ← SAMO User!
from passlib.hash import sha256_crypt
import re

application = Flask(__name__)
application.config.from_object(Configuration)

database.init_app(application)

jwt = JWTManager(application)


def is_valid_email(email):
    email_regex = r'^[^@]+@[^@]+\.[^@]{2,}$'
    return re.match(email_regex, email) is not None


def is_valid_password(password):
    return len(password) >= 8


@application.route("/register_customer", methods=["POST"])
def register_customer():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    if not forename:
        return jsonify({"message": "Field forename is missing."}), 400
    if not surname:
        return jsonify({"message": "Field surname is missing."}), 400
    if not email:
        return jsonify({"message": "Field email is missing."}), 400
    if not password:
        return jsonify({"message": "Field password is missing."}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Invalid email."}), 400

    if not is_valid_password(password):
        return jsonify({"message": "Invalid password."}), 400

    # da li mejl vec postoji
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Email already exists."}), 400

    hashed_password = sha256_crypt.hash(password)

    user = User(
        email=email,
        password=hashed_password,
        forename=forename,
        surname=surname,
        role="customer"
    )

    database.session.add(user)
    database.session.commit()

    return "", 200


@application.route("/register_courier", methods=["POST"])
def register_courier():
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    if not forename:
        return jsonify({"message": "Field forename is missing."}), 400
    if not surname:
        return jsonify({"message": "Field surname is missing."}), 400
    if not email:
        return jsonify({"message": "Field email is missing."}), 400
    if not password:
        return jsonify({"message": "Field password is missing."}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Invalid email."}), 400

    if not is_valid_password(password):
        return jsonify({"message": "Invalid password."}), 400


    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Email already exists."}), 400

    hashed_password = sha256_crypt.hash(password)

    user = User(
        email=email,
        password=hashed_password,
        forename=forename,
        surname=surname,
        role="courier"
    )

    database.session.add(user)
    database.session.commit()

    return "", 200


@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    if not email:
        return jsonify({"message": "Field email is missing."}), 400
    if not password:
        return jsonify({"message": "Field password is missing."}), 400

    if not is_valid_email(email):
        return jsonify({"message": "Invalid email."}), 400

    user = User.query.filter(User.email == email).first()

    if not user or not sha256_crypt.verify(password, user.password):
        return jsonify({"message": "Invalid credentials."}), 400

    additional_claims = {
        "forename": user.forename,
        "surname": user.surname,
        "roles": user.role
    }

    access_token = create_access_token(
        identity=user.email,
        additional_claims=additional_claims
    )

    return jsonify({"accessToken": access_token}), 200


@application.route("/delete", methods=["POST"])
@jwt_required()
def delete():
    email = get_jwt_identity()

    user = User.query.filter(User.email == email).first()

    if not user:
        return jsonify({"message": "Unknown user."}), 400

    database.session.delete(user)
    database.session.commit()

    return "", 200


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5000)