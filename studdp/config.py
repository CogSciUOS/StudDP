"""
loads and manages configuration for studdp. By default a configuration file at $HOME/.config/studdp/config.yaml is used.
"""
import logging
import time
import os
import ruamel.yaml as yaml
import keyring
import getpass
from .picker import Picker
import sys


log = logging.getLogger(__name__)

CONFIG_FILE = os.path.expanduser(os.path.join("~", ".config", "studdp", 'config.yml'))

DEFAULT_CONFIG = """\
######################################################
####################    Studdp    ####################
######################################################

# The base address of your universities stud.ip deployment. Change this if you don't study in Osnabrueck
base_address: 'https://studip.uos.de/plugins.php/restipplugin'

# The path to use as the root of the studdp downloads. The program will rebuild the course-structure of stud.ip under this root.
base_path: '~/studip'

# How often to check in seconds. This option is only respected when run as a daemon.
interval: 1200

# Your stud.ip username
username: 'ChangeMe!'

# Your stud.ip username is either stored in your keyring or read from this file if use_keyring is set to false.
use_keyring: true
password: 'optional' # only respected if use_keyring is false

# Your selected courses. You should not change this directly but rather use studdp -c to configure them
selected_courses:
  - '_course_id'

# All stud.ip nodes found here will be renamed as desired. By default one entry is created for every course in order to
# include the semester in the name. This works the same way for folders and documents. The ids can for example be
# easily found on studip using a browser.
namemap:
  '_course': '_title' # this is the format you should use. isn't yaml beautiful?

# Time of last check. You should normally not touch this
last_check: 0
"""

FILE_NOT_FOUND_TEXT = "Config file was not found under $HOME/.config/studdp/confyg.yaml. Default file has been created.\
                       Please configure the file before restarting the script."

# we are going to make the config class a Singleton
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    """
    Class for managing configuration. Should not be instantiated manullay. Rather use the instance provided as part of this module.
    """
    def __init__(self):
        self._settings = None
        self.load()

    # Emulate dict methods to allow key based access
    def __getitem__(self, item):
        return self._settings[item]

    def __setitem__(self, key, value):
        self._settings[key] = value

    def __delitem__(self, key):
        del self._settings[key]

    def __len__(self):
        return len(self._settings)

    def items(self):
        return self._settings.items()

    def keys(self):
        return self._settings.keys()

    def values(self):
        return self._settings.values()

    @property
    def auth(self):
        """
        tuple of (username, password). if use_keyring is set to true the password will be queried from the local keyring instead of taken from the
        configuration file.
        """
        username = self._settings["username"]

        if not username:
            raise ValueError("Username was not configured in %s" % CONFIG_FILE)

        if self._settings["use_keyring"]:
            password = self.keyring_get_password(username)
            if not password:
                self.keyring_set_password(username)
                password = self.keyring_get_password(username)
        else:
            password = self._settings["password"]

        return self._settings["username"], password

    def keyring_get_password(self, username):
        """
        get the password from the keyring provider currently in use by keyring
        """
        return keyring.get_password("StudDP", username)

    def keyring_set_password(self, username):
        password = getpass.getpass("Please enter password for user %s: " % username)
        keyring.set_password("StudDP", username, password)

    def keyring_del_password(self, username):
        keyring.delete_password("StudDP", username)

    def update_time(self):
        """
        Set the time of the last check to now
        """
        self._settings["last_check"] = time.time()

    def load(self, file=CONFIG_FILE):
        """
        load a configuration file. loads default config if file is not found
        """
        if not os.path.exists(file):
            print("Config file was not found under %s. Default file has been created" % CONFIG_FILE)
            self._settings = yaml.load(DEFAULT_CONFIG, yaml.RoundTripLoader)
            self.save(file)
            sys.exit()
        with open(file, 'r') as f:
            self._settings = yaml.load(f, yaml.RoundTripLoader)

    def save(self, file=CONFIG_FILE):
        """
        Save configuration to provided path as a yaml file
        """
        os.makedirs(os.path.dirname(file), exist_ok=True)
        with open(file, "w") as f:
            yaml.dump(self._settings, f, Dumper=yaml.RoundTripDumper, width=float("inf"))

    def namemap_lookup(self, node_id):
        """
        Look up a node id in the internal namemap.
        """
        try:
            return self._settings["namemap"][node_id]
        except KeyError:
            return None

    def namemap_set(self, node_id, name):
        """
        Link a node id to a name. The name and path properties of the node are changed accordingly
        """
        self._settings["namemap"][node_id] = name

    def selection_dialog(self, courses):
        """
        opens a curses/picker based interface to select courses that should be downloaded.
        """
        selected = list(filter(lambda x: x.course.id in self._settings["selected_courses"], courses))
        selection = Picker(
            title="Select courses to download",
            options=courses,
            checked=selected).getSelected()
        if selection:
            self._settings["selected_courses"] = list(map(lambda x: x.course.id, selection))
            self.save()
            log.info("Updated course selection")

    def is_selected(self, course):
        """
        checks if a course is in the list of selected courses.
        """
        return course.course.id in self._settings["selected_courses"]

    def selection(self):
        return self._settings["selected_courses"]

