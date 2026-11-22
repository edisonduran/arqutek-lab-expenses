FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml ./
COPY gastos ./gastos
RUN pip install --no-cache-dir . && mkdir /data

ENV GASTOS_FILE=/data/gastos.json
VOLUME /data
ENTRYPOINT ["gastos"]
