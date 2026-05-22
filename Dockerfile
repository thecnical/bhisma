# Bhisma Docker Image
FROM python:3.11-slim

LABEL maintainer="Bhisma Team"
LABEL description="AI-Powered Autonomous Multi-Protocol Offensive WiFi Framework"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    aircrack-ng \
    iw \
    wireless-tools \
    net-tools \
    libpcap-dev \
    libffi-dev \
    libssl-dev \
    gcc \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Install Bhisma in development mode
RUN pip install -e .

# Create non-root user (for safety)
RUN useradd -m -u 1000 bhisma

# Expose dashboard port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV BHISMA_CONFIG=/app/config.yaml

# Default command
CMD ["bhisma", "dashboard", "--host", "0.0.0.0", "--port", "8080"]
