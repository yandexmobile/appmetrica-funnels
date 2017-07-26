FROM python:2.7.13

RUN mkdir -p /usr/src
WORKDIR /usr/src

COPY requirements.txt /usr/src/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src

EXPOSE 5000

CMD [ "python", "./run.py" ]
