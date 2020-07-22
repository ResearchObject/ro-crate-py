FROM python:3.7-buster

COPY ./ /ro-crate-py
WORKDIR /ro-crate-py

RUN pip install --no-cache-dir -r requirements.txt && \
    python setup.py install
