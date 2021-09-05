FROM python:3

RUN mkdir -p /opt/src/election
WORKDIR /opt/src/election

COPY election/officialApp.py ./officialApp.py
COPY election/officialConfiguration.py ./officialConfiguration.py
COPY election/models.py ./models.py
COPY election/roleDecorator.py ./roleDecorator.py
COPY election/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH = "/opt/src/election"

ENTRYPOINT ["python", "./officialApp.py"]