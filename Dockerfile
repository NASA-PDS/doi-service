FROM python:3.7-slim

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY ./pds_doi_service /usr/src/app/pds_doi_service

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["-m", "pds_doi_service.api"]
