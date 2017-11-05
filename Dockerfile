FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD src/requirements.txt /code/
RUN pip install -r requirements.txt
RUN apt-get update
RUN apt-get -y install wkhtmltopdf
