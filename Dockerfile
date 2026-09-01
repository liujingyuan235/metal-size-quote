FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    HOST=0.0.0.0 \
    PORT=8090

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY calculator_server.py calculator.html backCal4cmd20251209.py ./
RUN mkdir -p /app/runtime

EXPOSE 8090

CMD ["python", "calculator_server.py"]
