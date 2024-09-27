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
COPY ./central_wallet.json /app/central_wallet.json

# Install Sugar CLI (assuming you want to use it from Cargo)
RUN cargo install sugar-cli

COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose the port your FastAPI app runs on
EXPOSE 8000

# Start the app
CMD ["/app/start.sh"]
