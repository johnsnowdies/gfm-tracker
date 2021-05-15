FROM python:3
ENV PYTHONUNBUFFERED 1
RUN apt-get update
RUN apt-get install postgresql-client -y
RUN apt-get install poppler-utils -y

RUN mkdir -p /var/log/gunicorn
RUN mkdir -p app

WORKDIR /app
COPY . /app/
RUN python -m pip install -r requirements.txt

CMD ["sh"]
