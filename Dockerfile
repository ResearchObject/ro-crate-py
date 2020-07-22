FROM python:3.7-buster

COPY ./ /ro-crate-py
WORKDIR /ro-crate-py

RUN pip3 install --no-cache-dir -r requirements.txt

# Dev Dockerfile: keep installation on separate RUN instruction
RUN python setup.py install
