FROM postgis/postgis:16-3.4-alpine

RUN apk add --no-cache --virtual .build-deps git build-base \
    && git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && cd /tmp/pgvector \
    && make with_llvm=no \
    && make install with_llvm=no \
    && rm -rf /tmp/pgvector \
    && apk del .build-deps

COPY init.sql /docker-entrypoint-initdb.d/init.sql
