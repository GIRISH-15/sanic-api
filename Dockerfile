FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# Expose port 8000 from the container
EXPOSE 8000

# Command to run the Sanic app
CMD ["python", "app.py"]
