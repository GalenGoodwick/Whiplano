# Use an official Rust image as the base
FROM rust:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    libssl-dev \
    pkg-config \
    build-essential

# Set the working directory
WORKDIR /app

# Copy only the requirements.txt to leverage Docker's caching mechanism
COPY requirements.txt .

# Create a virtual environment and install requirements
RUN python3 -m venv venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install -r requirements.txt

# Copy only the necessary directories and files after installing dependencies
COPY ./backend /app/backend
COPY ./collections /app/collections
COPY ./logs /app/logs
COPY ./config.json /app/config.json
COPY ./cache.json /app/cache.json

# Install Sugar CLI (assuming you want to use it from Cargo)
RUN cargo install sugar-cli

# Set environment variables
ENV PAYPAL_CLIENT_ID=AaHQKkslsJ0vBRvNmqIrpSV0e7ce6H_BUtZBBKN7Rneu80YaUShT0hN77BoevX4DogaGS30_eV81LfJT
ENV PAYPAL_CLIENT_SECRET=EMglT1YeSpSvPWBKUWuya5lGc5XE5Qw2KmUuQM7uyxZWFJnpiaN5DnC8oUw39GzcUn-3ErU2ELnwSMeN
ENV DATABASE_PASSWORD=gs5i03j24ykd45lu
ENV DATABASE_HOST=cvktne7b4wbj4ks1.chr7pe7iynqr.eu-west-1.rds.amazonaws.com
ENV DATABASE_USERNAME=iw7jod52a2lwbdv5
ENV DATABASE_NAME=k8ylxcd5jzsodvun
ENV CENTRAL_WALLET_PUBKEY=9QVeLdhziTQBFSTNWQxbzhwzQYgmcH4vT8GPsWqDBQFj
ENV CENTRAL_WALLET_KEY=[60,205,106,170,214,106,24,176,33,64,49,20,52,16,58,155,220,30,173,184,23,37,91,149,35,204,178,235,166,197,202,45,124,226,61,219,125,4,216,139,240,108,148,38,145,15,135,85,197,69,159,152,128,124,69,74,160,254,189,157,187,161,252,34]
ENV ALGORITHM=HS256
ENV ACCESS_TOKEN_EXPIRE_MINUTES=30
ENV GOOGLE_CLIENT_ID=97474372100-ef5fgjdrekfvlcviajsmtpnloeh800ol.apps.googleusercontent.com
ENV GOOGLE_CLIENT_SECRET=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
ENV GOOGLE_EMAIL_PASSWORD="sosq zuwh mfhi kudk"

# Expose the port your FastAPI app runs on
EXPOSE 8000

# Start the app
CMD ["/app/venv/bin/uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
