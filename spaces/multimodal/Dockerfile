FROM python:3.11-slim

WORKDIR /app

# Pillow's manylinux wheel covers libjpeg/libpng.
# Tesseract added in Phase 3 for the OCR Pre-Scan + Confidence Threshold defenses.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
