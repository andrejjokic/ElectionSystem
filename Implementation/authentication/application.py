from flask import Flask, request, Response, jsonify;
from configuration import Configuration;
from models import database, User, UserRole;
from email.utils import parseaddr;
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, create_refresh_token, get_jwt, get_jwt_identity;
from sqlalchemy import and_;
import json;
import re;

application = Flask ( __name__ );
application.config.from_object ( Configuration );

jwt = JWTManager ( application );

@application.route("/", methods = ["GET"])
def index():
    return Response("<h1>Welcome to authentication service index page!</h1>", status = 200);

@application.route("/register", methods = ["POST"])
def register():
    jmbg = request.json.get("jmbg", "");
    forename = request.json.get("forename", "");
    surname = request.json.get("surname", "");
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    if (len(jmbg) == 0):
        return Response(json.dumps({"message": "Field jmbg is missing."}), status = 400);

    if (len(forename) == 0):
        return Response(json.dumps({"message": "Field forename is missing."}), status = 400);

    if (len(surname) == 0):
        return Response(json.dumps({"message": "Field surname is missing."}), status = 400);

    if (len(email) == 0):
        return Response(json.dumps({"message": "Field email is missing."}), status = 400);

    if (len(password) == 0):
        return Response(json.dumps({"message": "Field password is missing."}), status = 400);

    # Check jmbg
    if (len(jmbg) != 13):
        return Response(json.dumps({"message": "Invalid jmbg."}), status = 400);

    day = int(jmbg[0:2]);
    month = int(jmbg[2:4]);
    region = int(jmbg[7:9]);
    k = int(jmbg[12]);

    if (day < 1 or day > 31 or month < 1 or month > 12 or region < 70):
        return Response(json.dumps({"message": "Invalid jmbg."}), status = 400);

    l = 11 - ((7 * (int(jmbg[0]) + int(jmbg[6])) + 6 * (int(jmbg[1]) + int(jmbg[7])) + 5 * (int(jmbg[2]) + int(jmbg[8])) +\
              4 * (int(jmbg[3]) + int(jmbg[9])) + 3 * (int(jmbg[4]) + int(jmbg[10])) + 2 * (int(jmbg[5]) + int(jmbg[11])) ) % 11);
    if (l > 9):
        l = 0;

    if (k != l):
        return Response(json.dumps({"message": "Invalid jmbg."}), status = 400);

    # Check email
    if ( not re.search("^\w+@[a-z]+\.[a-z]{2,3}$", email) ):
        return Response(json.dumps({"message": "Invalid email."}), status = 400);

    # Check password
    if (not re.search(".{8,}", password) or not re.search("\d+", password) or not re.search("[a-z]+", password) or not re.search("[A-Z]+", password)):
        return Response(json.dumps({"message": "Invalid password."}), status = 400);

    if (User.query.filter(User.email == email).first() is not None):
        return Response(json.dumps({"message": "Email already exists."}), status = 400);

    user = User (
        jmbg = jmbg,
        forename = forename,
        surname = surname,
        email = email,
        password = password
    );

    database.session.add(user);
    database.session.commit();

    userRole = UserRole (
        userId = user.id,
        roleId = 2          # official role id
    );

    database.session.add(userRole);
    database.session.commit();

    return Response(status = 200);

@application.route("/login", methods = ["POST"])
def login():
    email = request.json.get("email", "");
    password = request.json.get("password", "");

    if (len(email) == 0):
        return Response(json.dumps({"message": "Field email is missing."}), status = 400);

    if (len(password) == 0):
        return Response(json.dumps({"message": "Field password is missing."}), status = 400);

    # Check email
    if (not re.search("^\w+@[a-z]+\.[a-z]{2,3}$", email)):
        return Response(json.dumps({"message": "Invalid email."}), status=400);

    user = User.query.filter(and_(User.email == email, User.password == password)).first();

    if (user is None):
        return Response(json.dumps({"message": "Invalid credentials."}), status = 400);

    additionalClaims = {
        "jmbg": user.jmbg,
        "forename": user.forename,
        "surname": user.surname,
        "password": user.password,
        "roles": [str(role) for role in user.roles]
    }

    accessToken = create_access_token(identity = user.email, additional_claims = additionalClaims);
    refreshToken = create_refresh_token(identity = user.email, additional_claims = additionalClaims);

    return jsonify(accessToken = accessToken, refreshToken = refreshToken);

@application.route("/refresh", methods = ["POST"])
@jwt_required ( refresh = True )
def refresh():
    identity = get_jwt_identity();
    refreshClaims = get_jwt();

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "password": refreshClaims["password"],
        "roles": refreshClaims["roles"]
    };

    return jsonify(accessToken = create_access_token(identity = identity, additional_claims = additionalClaims));

@application.route("/delete", methods = ["POST"])
@jwt_required ()
def delete():
    # additionalClaims = get_jwt();
    #
    # if ("administrator" not in additionalClaims["roles"]):     # Not administator
    #     return Response(json.dumps({"message": "Permission denied!."}), status = 400);

    email = request.json.get("email", "");

    if (len(email) == 0):
        return Response(json.dumps({"message": "Field email is missing."}), status = 400);

    # Check email
    if (not re.search("^\w+@[a-z]+\.[a-z]{2,3}$", email)):
        return Response(json.dumps({"message": "Invalid email."}), status=400);

    user = User.query.filter(User.email == email).first();

    if (user is None):
        return Response(json.dumps({"message": "Unknown user."}), status = 400);

    UserRole.query.filter(UserRole.userId == user.id).delete();
    User.query.filter(User.email == email).delete();
    database.session.commit();

    return Response(status = 200);

if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0" , port = 5003 );