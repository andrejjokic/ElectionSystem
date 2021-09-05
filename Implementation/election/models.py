from flask_sqlalchemy import SQLAlchemy;

database = SQLAlchemy();

class PollNumber (database.Model):
    __tablename__ = "pollnumbers";

    id = database.Column(database.Integer, primary_key = True);
    pollNumber = database.Column(database.Integer, nullable = False);
    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable = False);
    participantId = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable = False);

    election = database.relationship("Election", back_populates = "pollNumbers");
    participant = database.relationship("Participant", back_populates = "pollNumbers");

class Vote (database.Model):
    __tablename__ = "votes";

    id = database.Column(database.Integer, primary_key = True);
    guid = database.Column(database.String(256), nullable = False);
    officialJMBG = database.Column(database.String(13), nullable = False);
    pollNumber = database.Column(database.Integer, nullable = False);
    electionId = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable = False);
    invalidVoteReason = database.Column(database.String(256));

    election = database.relationship("Election", back_populates = "votes");

class Election (database.Model):
    __tablename__ = "elections";

    id = database.Column(database.Integer, primary_key = True);
    start = database.Column(database.DateTime, nullable = False);
    end = database.Column(database.DateTime, nullable = False);
    individuals = database.Column(database.Integer, nullable = False);  # 1 - president election, 0 - parlament election

    participants = database.relationship("Participant", secondary = PollNumber.__table__, back_populates = "elections");
    pollNumbers = database.relationship("PollNumber", back_populates = "election");
    votes = database.relationship("Vote", back_populates = "election");

class Participant (database.Model):
    __tablename__ = "participants";

    id = database.Column(database.Integer, primary_key = True);
    name = database.Column(database.String(256), unique = True, nullable = False);
    individual = database.Column(database.Integer, nullable = False);  # 1 - president candidate, 0 - political party

    elections = database.relationship("Election", secondary = PollNumber.__table__, back_populates = "participants");
    pollNumbers = database.relationship("PollNumber", back_populates = "participant");