#!/bin/bash

echo "Waiting for database to be ready..."
sleep 10

echo "Creating database tables and owner account..."
python manage.py init_all

echo "Starting Flask application..."
python application.py












#python main.py --type all --authentication-url http://localhost:5000 --jwt-secret JWT_SECRET_DEV_KEY --roles-field roles --owner-role owner --customer-role customer --courier-role courier --customer-url http://localhost:5002 --owner-url http://localhost:5001 --courier-url http://localhost:5003 --with-authentication
#python main.py --type all --authentication-url http://localhost:5000 --jwt-secret JWT_SECRET_DEV_KEY --roles-field roles --owner-role owner --customer-role customer --courier-role courier --with-authentication --owner-url http://localhost:5001 --customer-url http://localhost:5002 --courier-url http://localhost:5003 --with-blockchain --provider-url http://localhost:8545 --owner-private-key 0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d

#docker-compose down -v
#docker-compose up --build

'''
application.py
query
min_price = request.args.get('min_price', type=float)
max_price = request.args.get('max_price', type=float)

if min_price is not None:
     query = query.filter(Product.price >= min_price)

if max_price is not None:
      query = query.filter(Product.price <= max_price)

all

configuration.py
isto samo bez JWT


models.py
isto kao owner


requriements.txt
bez JWT i blockhaina


DockerFile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x init.sh
EXPOSE 5004
CMD ["./init.sh"]


init.sh - opciono
#!/bin/bash

echo "Waiting for database to be ready..."
sleep 10

echo "Starting Public Flask application..."
python application.py

yml
public:
    build:
      context: ./public
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: mysql+pymysql://root:root@shopDB/shop
    depends_on:
      shopDB:
        condition: service_healthy
    ports:
      - "5004:5004"

Primer:
# login kao owner
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"onlymoney@gmail.com","password":"evenmoremoney"}'


kreiramo csv fajl
echo "Electronics,iPhone 15,999.99" > products.csv
echo "Electronics,AirPods,199.99" >> products.csv
echo "Clothing,T-Shirt,15.50" >> products.csv
echo "Clothing,Jeans,45.00" >> products.csv


# dodajemo proizvode
curl -X POST http://localhost:5001/update \
  -H "Authorization: Bearer eyJhbGc..." \
  -F "file=@products.csv"

testiranje
curl "http://localhost:5004/search"

filter po min/max price
curl "http://localhost:5004/search?min_price=50"    /   curl "http://localhost:5004/search?max_price=50"

kao range
curl "http://localhost:5004/search?min_price=20&max_price=200"

avi filteri
curl "http://localhost:5004/search?name=iPhone&category=Electronics&min_price=500&max_price=1500"




application.py

query

limit = request.args.get('limit', type=int)

if limit is not None and limit > 0:
        query = query.limit(limit)

all

curl "http://localhost:5004/search"

curl "http://localhost:5004/search?limit=3"

curl "http://localhost:5004/search?limit=1"

curl "http://localhost:5004/search?limit=0"

curl "http://localhost:5004/search?name=iPhone&limit=2"

curl "http://localhost:5004/search?category=Clothing&limit=1"

curl "http://localhost:5004/search?limit=-5"

docker --version
docker-compose --version

netstat -ano | findstr :5000
netstat -ano | findstr :5001
netstat -ano | findstr :5002
netstat -ano | findstr :5003
netstat -ano | findstr :8545
'''