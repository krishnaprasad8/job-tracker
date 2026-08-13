FROM python:3.12-slim

WORKDIR /app

# Copy requirements before the code so Docker can cache the pip layer —
# it only reinstalls when dependencies change, not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
