FROM python:3.8-alpine

WORKDIR /app

COPY requirements.txt .

RUN buildDeps='gcc musl-dev' \
    && apk add --no-cache $buildDeps \
    && pip3 install -r requirements.txt --no-cache-dir \
    && apk del $buildDeps

COPY . .

CMD ["python3", "-m", "blbot"]
