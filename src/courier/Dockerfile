FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# solidity instaliran
RUN python -c "from solcx import install_solc; install_solc('0.8.0')"

COPY . .
RUN chmod +x init.sh

EXPOSE 5003

CMD ["./init.sh"]