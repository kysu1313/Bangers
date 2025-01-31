
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y python3.9 python3.9-dev && apt-get install pip -y
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "app.py"]