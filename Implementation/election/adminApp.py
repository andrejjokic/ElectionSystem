import json, pytz;
import os
import time

from dateutil import parser;
from dateutil.parser import ParserError;
from flask import Flask, request, Response, jsonify;
from flask_jwt_extended import JWTManager;
from datetime import datetime, timedelta;

from roleDecorator import roleCheck;
from adminConfiguration import Configuration;
from models import database, Participant, Election, PollNumber;

application = Flask ( __name__ );
application.config.from_object ( Configuration )
jwt = JWTManager ( application );

@application.route("/", methods = ["GET"])
@roleCheck(role = "administrator")
def index():
    return "<h1>Welcome to admin index page!</h1>";

@application.route("/createParticipant", methods = ["POST"])
@roleCheck(role = "administrator")
def createParticipant():

    name = request.json.get("name","");
    individual = request.json.get("individual", "");

    if (len(name) == 0):
        return Response(json.dumps({"message": "Field name is missing."}), status=400);

    if (individual != True and individual != False and len(individual) == 0):
        return Response(json.dumps({"message": "Field individual is missing."}), status=400);

    if (Participant.query.filter(Participant.name == name).first() is not None):
        return Response(json.dumps({"message": "Participant name already exists."}), status = 400);

    participant = Participant(
        name = name, individual = individual
    );

    database.session.add(participant);
    database.session.commit();

    return jsonify(id = participant.id);

@application.route("/getParticipants", methods = ["GET"])
@roleCheck(role = "administrator")
def getParticipants():
    participants = [{
        "id": item.id,
        "name": item.name,
        "individual": bool(item.individual)
    } for item in Participant.query.all()];
    return jsonify(participants = participants);

@application.route("/createElection", methods = ["POST"])
@roleCheck(role = "administrator")
def createElection():
    start = request.json.get("start","");
    end = request.json.get("end", "");
    individual = request.json.get("individual", "");
    participants = request.json.get("participants", "");


    if (len(start) == 0):
        return Response(json.dumps({"message": "Field start is missing."}), status=400);

    if (len(end) == 0):
        return Response(json.dumps({"message": "Field end is missing."}), status=400);

    if (individual != True and individual != False and len(individual) == 0):
        return Response(json.dumps({"message": "Field individual is missing."}), status=400);

    if (participants == ""):
        return Response(json.dumps({"message": "Field participants is missing."}), status=400);

    try:
        start = parser.parse(start);
        end = parser.parse(end);
    except ParserError:
        return Response(json.dumps({"message": "Invalid date and time."}), status = 400);

    if (start > end):
        return Response(json.dumps({"message": "Invalid date and time."}), status = 400);

    elections = Election.query.all();

    for election in elections:
         if ((election.start <= start <= election.end) or\
                (election.start <= end <= election.end) or\
                (start <= election.start and end >= election.end)):
            return Response(json.dumps({"message": "Invalid date and time."}), status = 400);


    participantIds = request.json["participants"];
    individual = request.json["individual"];

    if (len(participantIds) < 2):
        return Response(json.dumps({"message": "Invalid participants."}), status = 400);

    for participantId in participantIds:
        participant = Participant.query.filter(Participant.id == participantId).first();
        if (participant is None or participant.individual != individual):
            return Response(json.dumps({"message": "Invalid participants."}), status = 400);

    election = Election(
        start = start, end = end, individuals = individual
    );

    database.session.add(election);
    database.session.commit();

    currPollNumber = 1;
    pollNumbers = [];

    for participantId in participantIds:
        pollNumber = PollNumber(
            pollNumber = currPollNumber, electionId = election.id, participantId = participantId
        );
        database.session.add(pollNumber);
        database.session.commit();

        pollNumbers.append(currPollNumber);
        currPollNumber = currPollNumber + 1;

    return  jsonify(pollNumbers = pollNumbers);

@application.route("/getElections", methods = ["GET"])
@roleCheck(role = "administrator")
def getElections():
    elections = [{
        "id": item.id,
        "start": str(item.start),
        "end": str(item.end),
        "individual": bool(item.individuals),
        "participants": [{
            "id": it.id,
            "name": it.name
        } for it in item.participants]
                  } for item in Election.query.all()];

    return jsonify(elections = elections);


# noinspection PyShadowingBuiltins
@application.route("/getResults", methods = ["GET"])
@roleCheck(role = "administrator")
def getResults():
    if ("id" not in request.args or request.args["id"] == ""):
        return Response(json.dumps({"message": "Field id is missing."}), status = 400);

    id = int(request.args["id"]);
    election = Election.query.filter(Election.id == id).first();

    if (election is None):
        return Response(json.dumps({"message": "Election does not exist."}), status = 400);

    # now = datetime.utcnow().replace(tzinfo = pytz.utc);
    now = datetime.now();
    now = now + timedelta(seconds=2)        # Added to overcome time lag

    if (election.end > now):
        return Response(json.dumps({"message": "Election is ongoing."}), status = 400);

    results = getResultsLocal(election);

    participants = [{
        "pollNumber": item.pollNumber,
        "name": item.participant.name,
        "result": results[item.pollNumber]
    } for item in election.pollNumbers];

    invalidVotes = [{
        "electionOfficialJmbg": item.officialJMBG,
        "ballotGuid": item.guid,
        "pollNumber": item.pollNumber,
        "reason": item.invalidVoteReason
    } for item in election.votes if (item.invalidVoteReason is not None)];

    return jsonify(participants = participants, invalidVotes = invalidVotes);

def getResultsLocal(election):
    if (election.individuals == 1):
        result = {};
        for i in election.pollNumbers:
            myVotes = len([item for item in election.votes if (item.pollNumber == i.pollNumber and item.invalidVoteReason is None)]);
            result[i.pollNumber] = round(myVotes / len(election.votes), 2);

        return result;
    else:
        votes = {};
        for i in election.pollNumbers:
            votes[i.pollNumber] = len([item for item in election.votes if (item.pollNumber == i.pollNumber and item.invalidVoteReason is None)]);

        t_votes = votes.copy();
        for key in votes:
            if (votes[key] / len(election.votes) < 0.05):
                t_votes.pop(key);

        seats = {};
        for key in votes:
            seats[key] = 0;

        while (sum(seats.values()) < 250):
            max_v = max(t_votes.values());
            next_seat = list(t_votes.keys())[list(t_votes.values()).index(max_v)];
            seats[next_seat] += 1;
            t_votes[next_seat] = votes[next_seat]/(seats[next_seat] + 1);

        return seats;

if (__name__ == "__main__"):
    os.environ['TZ'] = 'Europe/Belgrade';
    time.tzset()
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5001 );
