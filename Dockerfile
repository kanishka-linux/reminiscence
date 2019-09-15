From python:3.6-slim-stretch

WORKDIR /usr/src/reminiscence

RUN apt-get update \
  && apt-get install --no-install-recommends -y chromium netcat wget \
  && wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.stretch_amd64.deb \
  && apt-get install -y ./wkhtmltox_0.12.5-1.stretch_amd64.deb \
  && rm ./wkhtmltox_0.12.5-1.stretch_amd64.deb \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . /usr/src/reminiscence

RUN mkdir -p logs archive tmp \
  && python manage.py applysettings --docker yes \
  && python manage.py generatesecretkey
