# Gunakan Python resmi berbasis Debian/Ubuntu
FROM python:3.11

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt update && apt install -y build-essential cmake && \
    pip install --no-cache-dir numpy python-jobspy flask

# Copy aplikasi
COPY . .

# Expose Flask port
EXPOSE 5000

# Jalankan aplikasi
CMD ["python", "app.py"]
