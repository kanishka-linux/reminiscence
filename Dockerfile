From python:3.6

WORKDIR /usr/src/reminiscence

COPY requirements.txt ./

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y netcat chromium

RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.stretch_amd64.deb

RUN apt-get install -y ./wkhtmltox_0.12.5-1.stretch_amd64.deb

RUN pip install -r requirements.txt

ADD . /usr/src/reminiscence

RUN mkdir -p logs archive tmp

RUN python manage.py applysettings --docker yes

RUN python manage.py generatesecretkey
