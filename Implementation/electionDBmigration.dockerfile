FROM python:3

RUN mkdir -p /opt/src/election
WORKDIR /opt/src/election

COPY election/migrate.py ./migrate.py
COPY election/models.py ./models.py
COPY election/adminConfiguration.py ./adminConfiguration.py
COPY election/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./migrate.py"]