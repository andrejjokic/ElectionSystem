import os;

class Configuration():
    JWT_SECRET_KEY = "JWT_SECRET_KEY";
    JSON_SORT_KEYS = False;
    REDIS_HOST = os.environ["REDIS_HOST"];
    REDIS_VOTES_LIST = "votes";