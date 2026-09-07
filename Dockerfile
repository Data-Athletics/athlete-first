FROM python:3.14.2 AS BASE

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r requirements.txt


FROM BASE AS DEV

WORKDIR /app

CMD [ "python", "app/main.py" ]


FROM BASE AS TEST

CMD [ "pytest" ]


FROM BASE AS PROD

COPY . .

CMD [ "python", "main.py" ]