FROM python:3

RUN mkdir -p /opt/src/election
WORKDIR /opt/src/election

COPY election/daemonApp.py ./daemonApp.py
COPY election/daemonConfiguration.py ./daemonConfiguration.py
COPY election/models.py ./models.py
COPY election/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH = "/opt/src/election"

ENTRYPOINT ["python", "./daemonApp.py"]