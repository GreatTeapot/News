FROM python:3.11.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN  pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .


RUN chmod a+x /app/docker/*.sh



