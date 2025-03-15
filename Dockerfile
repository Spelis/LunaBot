FROM python:3.13.1
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
        texlive-full \
        biber \
        latexmk && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /opt/lunabot
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python3", "main.py"]
