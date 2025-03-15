FROM python:3.13.1
FROM texlive/texlive:latest
WORKDIR /opt/lunabot
COPY requirements.txt .
RUN apt-get update && apt-get install -y python3-pip && pip3 install -r requirements.txt
COPY . .
CMD ["python3", "main.py"]
