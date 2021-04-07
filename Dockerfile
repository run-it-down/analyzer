FROM python:3.8-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y postgresql gcc
RUN pip install --upgrade pip setuptools wheel

ADD analyzer /analyzer/
ADD common /common/
COPY requirements.txt .

RUN pip install -r requirements.txt
RUN pip install scipy
RUN pip install scikit-learn

ARG DBHOST_ARG
ARG DBPORT_ARG
ARG DBUSER_ARG
ARG DBPASSWD_ARG
ARG DB_ARG

ENV DBHOST=$DBHOST_ARG
ENV DBPORT=$DBPORT_ARG
ENV DBUSER=$DBUSER_ARG
ENV DBPASSWD=$DBPASSWD_ARG
ENV DB=$DB_ARG
ENV PYTHONPATH "/analyzer/:/common/common/"
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8003", "analyzer.api", "--timeout", "600"]
