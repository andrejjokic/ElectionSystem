from daemonConfiguration import Configuration;
from redis import Redis;
from models import database, Election, Vote;
from datetime import datetime;
from flask import Flask
import pytz
import os
import time

os.environ['TZ'] = 'Europe/Belgrade';
time.tzset()
application = Flask(__name__);
application.config.from_object (Configuration);
database.init_app(application);
# application.app_context().push();

while True:
    try:
        with Redis(host = Configuration.REDIS_HOST) as redis:
            while True:
                bytesStream = redis.blpop(Configuration.REDIS_VOTES_LIST)[1];
                line = bytesStream.decode("utf-8");
                data = line.split(";");
                # now = datetime.utcnow().replace(tzinfo = pytz.utc);
                now = datetime.now().replace(microsecond=0)

                with application.app_context() as context:
                    elections = Election.query.all();
                    election = None;
                    for item in elections:
                        if (item.start <= now <= item.end):
                            election = item;
                            break;

                    if (election is None):
                        continue;

                    if (Vote.query.filter(Vote.guid == data[0]).first() is not None):
                        duplicateBallot = Vote(
                            guid = data[0],
                            officialJMBG = data[2],
                            pollNumber = int(data[1]),
                            electionId = election.id,
                            invalidVoteReason = "Duplicate ballot."
                        );
                        database.session.add(duplicateBallot);
                        database.session.commit();
                        continue;

                    if (int(data[1]) not in [item.pollNumber for item in election.pollNumbers]):
                        invalidPoll = Vote(
                            guid = data[0],
                            officialJMBG = data[2],
                            pollNumber = int(data[1]),
                            electionId = election.id,
                            invalidVoteReason = "Invalid poll number."
                        );
                        database.session.add(invalidPoll);
                        database.session.commit();
                        continue;

                    vote = Vote(
                        guid = data[0],
                        officialJMBG = data[2],
                        pollNumber = int(data[1]),
                        electionId = election.id,
                    );
                    database.session.add(vote);
                    database.session.commit();
    except Exception as error:
        print(error)