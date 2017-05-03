import os
import yaml
import time
from .picker import Picker

CONFIG_FILE = os.path.expanduser(os.path.join("~", ".config", "studdp", 'config.yml'))

DEFAULT_CONFIG = {
    "username": "",
    "base_address": "https://studip.uos.de/plugins.php/restipplugin",
    "base_path": "~/studip",
    "interval": 1200,
    "last_check": -1,
    "password": "",
    "use_keyring": True,
    "selected_courses": [],
    "namemap": {}
}

FILE_NOT_FOUND_TEXT = "Config file was not found under $HOME/.config/studdp/confyg.yaml. Default file has been created.\
                       Please configure the file before restarting the script."


class _Conf:
    def __init__(self):
        self.config = None
        self.load_config()

    @property
    def auth(self):
        return self.config["username"], self.config["password"]

    def update_time(self):
        self.config["last_check"] = time.time()
        self.save_config()

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self.save_config(DEFAULT_CONFIG)
            raise FileNotFoundError(FILE_NOT_FOUND_TEXT)
        with open(CONFIG_FILE, 'r') as f:
            self.config = yaml.load(f)

    def save_config(self, config=None):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            if config is not None:
                yaml.dump(config, f, default_flow_style=False)
            else:
                yaml.dump(self.config, f, default_flow_style=False)

    def namemap_lookup(self, node_id):
        try:
            return self.config["namemap"][node_id]
        except KeyError:
            return None

    def namemap_set(self, node_id, name):
        self.config["namemap"][node_id] = name
        self.save_config()

    def selection_dialog(self, courses):
        selected = list(filter(lambda x: x.course.id in self.config["selected_courses"], courses))
        selection = Picker(
            title="Select courses to download",
            options=courses,
            checked=selected).getSelected()
        if selection:
            self.config["selected_courses"] = list(map(lambda x: x.course.id, selection))
            self.save_config()

    def is_selected(self, course):
        return course.course.id in self.config["selected_courses"]


configuration = _Conf()
