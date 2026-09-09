FROM python:3.12-alpine

RUN adduser -D -u 1000 mintranet \
    && mkdir -p /data \
    && chown mintranet:mintranet /data

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

USER mintranet
EXPOSE 8081
ENV MINTRANET_DATA_DIR=/data
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
