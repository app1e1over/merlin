FROM python:3.10
RUN apt-get update && apt-get install -y libsqlite3-dev
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "./app.py"]
