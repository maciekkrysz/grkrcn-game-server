# syntax=docker/dockerfile:1
FROM python:3.9
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN apt update
RUN apt-get -y install libxmlsec1-dev pkg-config
RUN /usr/local/bin/python -m pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt
COPY . /code/