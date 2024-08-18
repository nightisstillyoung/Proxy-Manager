FROM python:3.11

RUN ["mkdir", "/proxy_manager"]

WORKDIR /proxy_manager

COPY requirements.txt .

RUN ["pip", "install", "-r", "requirements.txt"]

COPY . .

WORKDIR src
