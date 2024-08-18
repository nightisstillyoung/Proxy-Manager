from pathlib import Path
from dotenv import load_dotenv
import os
import yaml


# If you want to use LibYAML bindings, which are much faster than the pure Python version, you need to download and
# install LibYAML. Then you may build and install the bindings by executing
# $ python setup.py --with-libyaml install
# source: https://pyyaml.org/wiki/PyYAMLDocumentation
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


# load environment variables from .env-dev file
load_dotenv()

# database
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")

# redis
REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = os.environ.get("REDIS_PORT")

# user simple auth
# WARNING: off it only if you use it on your localhost or with another webserver (For example, NGINX)
AUTH = os.environ.get("AUTH", False)

# credentials are stored in sha256 format
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")

# EXPIRES (hours) time for session cookie
# -1 for infinite
EXPIRES = int(os.environ.get("EXPIRES"))

# against rainbow tables
SALT = os.environ.get("SALT")

# is DEVELOPMENT
DEV = os.environ.get("DEV", default=False)


# ==== yaml configs ====
p = Path(__file__)

# checker
with open(p.with_name("checker.yaml")) as file:
    checker_config: dict = yaml.load(file, Loader=Loader)


# redis
# Redis(**redis_config)
with open(p.with_name("redis.yaml")) as file:
    redis_config: dict = yaml.load(file, Loader=Loader)
    redis_config["host"] = REDIS_HOST
    redis_config["port"] = REDIS_PORT


# website config
with open(p.with_name("website.yaml")) as file:
    website_config: dict = yaml.load(file, Loader=Loader)
