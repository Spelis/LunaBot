FROM python:3.13.1
FROM texlive/texlive:latest
WORKDIR /opt/lunabot
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "main.py"]
