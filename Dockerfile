FROM python:3.12-slim

# /code, not /app, so it isn't confused with the app/ package copied into it.
WORKDIR /code

# Copy requirements before the code so Docker can cache the pip layer —
# it only reinstalls when dependencies change, not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
