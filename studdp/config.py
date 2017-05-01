import os
import yaml

CONFIG_FILE = os.path.expanduser(os.path.join("~", ".config", "studdp", 'config.yml'))

DEFAULT_CONFIG = {
    "username": "",
    "base_address": "https://studip.uos.de/plugins.php/restipplugin",
    "local_path": "~/studip",
    "interval": 1200,
    "last_check": -1,
    "courses_selected": False,
    "selected_courses": [],
    "namemap": {}
}

FILE_NOT_FOUND_TEXT = "Config file was not found under $HOME/.config/studdp/confyg.yaml. Default file has been created.\
                       Please configure the file before restarting the script."

class Conf:
    def __init__(self):
        self.config = None
        self.load_config()
        self.namemap = self.get_namemap(self.config["namemap"])
        self.base_address = self.config["base_address"]

    @property
    def auth(self):
        return self.config["username"], self.config["password"]

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

    def get_namemap(self, *args, **kwargs):
        class NameMap:
            def __init__(iself, config):
                iself.map = config

            def lookup(iself, node_id):
                try:
                    return iself.map[node_id]
                except KeyError:
                    return None

            def set(iself, node_id, name):
                iself.map[node_id] = name
                self.save_config()
        return NameMap(*args, **kwargs)

configuration = Conf()
