FROM python:3

RUN mkdir -p /opt/src/election
WORKDIR /opt/src/election

COPY election/adminConfiguration.py ./adminConfiguration.py
COPY election/models.py ./models.py
COPY election/roleDecorator.py ./roleDecorator.py
COPY election/requirements.txt ./requirements.txt
COPY election/adminApp.py ./adminApp.py

RUN pip install -r ./requirements.txt

ENV PYTHONPATH = "/opt/src/election"

ENTRYPOINT ["python", "./adminApp.py"]

