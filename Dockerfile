FROM python:3.8.12-alpine3.14

LABEL maintainer="Data Tropics <https://www.data-tropics.com>"

RUN apk add --no-cache \
    bash=5.1.4-r0 \
    && rm -rf /var/cache/apk/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r ./requirements.txt

COPY *.py ./

CMD ["bash"]
