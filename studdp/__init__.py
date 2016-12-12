import json
import os

CONFIG_FILE = os.path.expanduser(
    os.path.join("~", ".config", "studdp", 'config.json'))

if not os.path.exists(CONFIG_FILE):
    print('No config file found. Please make sure the is one provided at %s. Exiting.' % CONFIG_FILE)
    exit(1)

with open(CONFIG_FILE, 'r') as rfile:
    CONFIG = json.load(rfile)
