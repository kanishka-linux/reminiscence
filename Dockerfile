From python:3.6

WORKDIR /usr/src/reminiscence

COPY requirements.txt ./

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y wkhtmltopdf xvfb netcat

RUN pip install -r requirements.txt

ADD . /usr/src/reminiscence

RUN mkdir -p logs archive

RUN python manage.py applysettings --docker yes

RUN python manage.py generatesecretkey

RUN python manage.py nltkdownload
