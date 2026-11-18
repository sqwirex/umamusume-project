FROM python:3.15-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /data
ENV DB_PATH=/data/umamusume.db
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python", "app.py"]
