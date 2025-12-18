import os;
from datetime import timedelta;

class Configuration():
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "mysql+pymysql://root:root@localhost/authentication");
    JWT_SECRET_KEY = "JWT_SECRET_DEV_KEY";
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1);
    SQLALCHEMY_TRACK_MODIFICATIONS = False;  #da mi ubrza izvrsavanje aplikacije