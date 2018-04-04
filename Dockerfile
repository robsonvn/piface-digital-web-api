FROM resin/raspberrypi3-python:3.6.1-slim
MAINTAINER Robson Nascimento robsonvnasc@gmail.com

WORKDIR /usr/src/app

RUN apt update -y && apt install -y python3-pifacedigitalio

COPY src/ .

RUN mv logging.conf.example logging.conf && mv .env.example .env
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY help/spi.py /usr/lib/python3/dist-packages/pifacecommon/spi.py

EXPOSE 80

CMD ["python", "-m", "aiohttp.web", "-H" ,"0.0.0.0", "-P", "80", "app:init_func"]

