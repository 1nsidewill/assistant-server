FROM python:3.11.6-slim
WORKDIR /app 

## Copy all src files
COPY ./ .

## Install packages
RUN apt-get update  && \
    apt-get install -y build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools poetry

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

# RUN chmod +x entrypoint

## Run the application on the port 8005
EXPOSE 8005

#ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["sh", "entrypoint.sh"]