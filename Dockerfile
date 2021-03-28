FROM alpine:3.12.0

RUN apk update
RUN apk add postgresql-dev gcc python3-dev musl-dev
RUN apk add python3
RUN apk add --update py-pip
RUN pip install --upgrade pip

ADD analyzer /analyzer/
ADD common /common/
COPY requirements.txt .

RUN pip install -r requirements.txt

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
