FROM python:3.7-alpine

RUN apk add build-base jpeg-dev zlib-dev

RUN pip install fastapi[all]
RUN pip install pika
RUN pip install retry
RUN pip install imageio
RUN pip install numpy
RUN pip install aiohttp

WORKDIR /src
COPY ml2api/ /src/ml2api/
COPY example/ /src/
ENV PYTHONPATH=/src
