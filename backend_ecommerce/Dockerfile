FROM python:3.11-slim

WORKDIR /app

# Copy requirements from inner folder
COPY backend_ecommerce/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy full backend source
COPY backend_ecommerce/ .

EXPOSE 5000

CMD ["python", "app.py"]
