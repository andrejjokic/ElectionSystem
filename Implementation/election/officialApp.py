import io, csv, json;

from flask import Flask, request, Response;
from officialConfiguration import Configuration;
from models import database;
from flask_jwt_extended import JWTManager, get_jwt;
from roleDecorator import roleCheck;
from redis import Redis;

application = Flask ( __name__ );
application.config.from_object ( Configuration )
jwt = JWTManager ( application );

@application.route("/", methods = ["GET"])
@roleCheck(role = "user")
def index():
    return Response("<h1>Welcome to election official index page!</h1>", status = 200);

@application.route("/vote", methods = ["POST"])
@roleCheck(role = "user")
def vote():
    if ("file" not in request.files):
        return Response(json.dumps({"message": "Field file is missing."}), status = 400);

    content = request.files["file"].stream.read().decode("utf-8");
    stream = io.StringIO(content);
    reader = csv.reader(stream);

    i = 0;
    for row in reader:
        if (len(row) != 2):
            return Response(json.dumps({"message": f"Incorrect number of values on line {i}."}), status = 400);
        try:
            if (int(row[1]) < 1):
                return Response(json.dumps({"message": f"Incorrect poll number on line {i}."}), status=400);
        except:
            return Response(json.dumps({"message": f"Incorrect poll number on line {i}."}), status=400);
        i = i + 1;

    additionalClaims = get_jwt();
    # Reset stream cursorO
    stream.seek(0);
    reader = csv.reader(stream);

    with Redis(host = Configuration.REDIS_HOST) as redis:
        for row in reader:
            redis.rpush(Configuration.REDIS_VOTES_LIST, row[0] + ";" + row[1] + ";" + additionalClaims["jmbg"]);


    return Response(status = 200);

if (__name__ == "__main__"):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5002 );