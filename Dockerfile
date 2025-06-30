FROM python:3.13.1-slim AS builder
WORKDIR /install

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc libffi-dev python3-dev libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install/deps -r requirements.txt

FROM python:3.13.1-slim AS runtime
WORKDIR /project3
COPY  --from=builder /install/deps /usr/local
COPY . .
ENTRYPOINT ["python", "main.py"]