FROM python:3-slim

WORKDIR /usr/src/app

COPY requirments.txt ./
RUN pip install --no-cache-dir -r requirments.txt

COPY ./ ./

CMD [ "python", "-u", "./main.py" ]
