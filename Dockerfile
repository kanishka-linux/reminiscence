FROM python:3.10-slim-bookworm

WORKDIR /usr/src/reminiscence

RUN apt-get update \
  && apt-get install --no-install-recommends -y netcat-traditional htop \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . /usr/src/reminiscence

RUN mkdir -p logs archive tmp \
  && python manage.py applysettings --docker yes \
  && python manage.py generatesecretkey
