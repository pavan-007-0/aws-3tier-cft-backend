FROM python:3.11-slim

WORKDIR /app

# copy requirements from inner backend_ecommerce folder
COPY backend_ecommerce/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# copy full backend source
COPY backend_ecommerce/ /app/

EXPOSE 5000

CMD ["python", "app.py"]
