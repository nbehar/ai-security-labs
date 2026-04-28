FROM python:3.11-slim

WORKDIR /app

# Pillow's manylinux wheel bundles libjpeg/libpng; no apt deps needed for v1.
# Tesseract will be added in Phase 3 when the OCR Pre-Scan defense lands.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
