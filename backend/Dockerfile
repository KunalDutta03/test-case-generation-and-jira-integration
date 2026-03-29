FROM python:3.11-slim

WORKDIR /app

# Install system deps for PyMuPDF, psycopg2
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libgl1-mesa-glx libgomp1 gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads /app/faiss_index

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
