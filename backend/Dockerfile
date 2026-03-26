FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*


# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories for the app
RUN mkdir -p uploads temp_recordings

# Copy the entire backend directory into the container
COPY . .

# Hugging Face Spaces requires the app to listen on port 7860
EXPOSE 7860

# Start the uvicorn server, binding to 0.0.0.0 on port 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
