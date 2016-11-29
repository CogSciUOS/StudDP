#!/usr/bin/env python3

"""
StudDP downloads files from Stud.IP.
"""

import json
import logging
import os
import shutil
import signal
import time
import sys
import requests
import re
import optparse
from distutils.util import strtobool
import keyring
import getpass

LOG = logging.getLogger(__name__)
LOG_PATH = os.path.expanduser(os.path.join('~', '.studdp'))
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
PID_FILE = os.path.expanduser(os.path.join('~', '.studdp', 'studdp.pid'))

class APIWrapper(object):
    """
    An API wrapper for the Stud.IP Rest.API.
    See studip.github.io/studip-rest.ip/ for details.
    """

    def __init__(self, configuration):
        """
        Initializes the API's auth and base address.
        """
        self.__auth = (configuration['username'], get_password(configuration["username"]))
        self.__base_address = configuration['base_address']
        self.__local_path = os.path.expanduser(configuration['local_path'])

    def __url__(self, route):
        """
        Creates an URL from the configuration and the route.
        """
        return "{}{}".format(self.__base_address, route)

    def __get(self, route, stream=False):
        """
        Performs a GET request with the authentication from the configuration.
        """
        try:
            return requests.get(self.__url__(route), auth=self.__auth, stream=stream)
        except (TimeoutError,
                requests.packages.urllib3.exceptions.NewConnectionError,
                requests.packages.urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError) as error:
            LOG.error("Error on get %s: %s", route, error)
            return

    def get_courses(self, semester_id=False):
        """
        Gets a list of courses.
        Either for all, or if specified, for a semester with a specific ID.
        """
        try:
            path = '/api/courses'
            if semester_id:
                LOG.info('Getting only courses for semester with ID %s', semester_id)
                path += '/semester/{}'.format(semester_id)
            return json.loads(self.__get(path).text)['courses']
        except (ValueError, AttributeError):
            return []

    def __get_course_folders(self, course):
        """
        Gets a list of document folders for a given course id.
        """
        try:
            return json.loads(
                self.__get('/api/documents/{}/folder'.format(course['course_id'])).text
                )['folders']
        except (ValueError, AttributeError):
            return []

    def get_documents(self, course):
        """
        Gets a list of documents and folders inside a folder.
        """
        documents = []
        folders = self.__get_course_folders(course)
        for i, folder in enumerate(folders):
            folders[i]['path'] = os.path.join(self.__local_path, course['title'])

        import traceback
        while folders:
            folder = folders.pop()
            path = '/api/documents/{}/folder/{}' \
                    .format(course['course_id'], folder['folder_id'])

            count = 0
            try:
                txt = ''
                while not txt and count < 10:
                    txt = self.__get(path).text
                    if 'HTTP/1.1 401 Unauthorized' == txt:
                        txt = ''
                        time.sleep(0.5)
                        count += 1
                temp = json.loads(txt)
            except (ValueError, AttributeError) as e:
                LOG.error('Error on loading %s. %s', path, e)
                continue

            for key in ['folders', 'documents']:
                for i in range(len(temp[key])):
                    temp[key][i]['path'] = os.path.join(folder['path'],
                                                        folder['name'])
            documents += temp['documents']
            folders += temp['folders']
        return documents

    def download_document(self, document, docfile):
        """
        Downloads the document to docfile.
        """
        try:
            shutil.copyfileobj(self.__get('/api/documents/{}/download'.format(document['document_id']),
                                      stream=True).raw, docfile)
        except AttributeError as attribute_error:
            LOG.error('Can not download file {}, {}'.format(document['document_id'], attribute_error))

class StudDP(object):
    """
    The main program loops until interrupted.
    Every time files were changed after the last check, they are downloaded.
    Files are also downloaded if they do not exist locally.
    """

    def __init__(self, config, exit_on_loop, on_windows, update):
        """
        Initializes the API and the update frequencies.
        """
        self.config = config
        self.interval = self.config['interval']
        self.api = APIWrapper(self.config)
        self.exit_on_loop = exit_on_loop
        self.on_windows = on_windows
        self.update = update

    def __needs_download(self, document):
        """
        Checks if a download of the document is needed.
        """
        return ((int(document['chdate']) > self.config['last_check']) and \
               self.update) or not \
               os.path.exists(os.path.join(document['path'],
                                           document['filename']))

    def __call__(self):
        """
        Starts the main loop and checks periodically for document changes and downloads.
        """
        while True:
            courses = self.api.get_courses()

            if not self.config['courses_selected']:
                LOG.info("Updating course selection")
                self.config["selected_courses"] = []
                for course in courses:
                    title = course['title']
                    if user_yes_no_query('Download files for %s?' % title):
                        self.config['selected_courses'].append(title)
                        LOG.info('%s chosen for download', title)
                    else:
                        LOG.info('%s not chosen for download', title)
                        
            LOG.info('Checking courses.')
            for course in courses:
                title = course['title']
                LOG.info('Course: %s', title)

                if title in self.config['selected_courses']:
                    LOG.info('Downloading files for %s', title)
                    documents = self.api.get_documents(course)
                    for document in documents:
                        if self.on_windows:
                            document["path"] = re.sub(":", "", document["path"])
                            document["filename"] = re.sub(":", "", document["filename"])
                        if self.__needs_download(document):
                            path = os.path.join(document['path'], document['filename'])
                            LOG.info('Downloading %s...', path)
                            os.makedirs(document['path'], exist_ok=True)
                            with open(path, 'wb') as docfile:
                                self.api.download_document(document, docfile)
                            LOG.info('Downloaded %s', path)
                else:
                    LOG.info('Skipping files for %s', title)
            self.config['last_check'] = time.time()
            self.config['courses_selected'] = True
            LOG.info('Done checking.')
            if self.exit_on_loop:
                exit_func()
            time.sleep(self.interval)

def get_password(username):
    LOG.info("Querying for password")
    password = keyring.get_password("StudDP", username)
    if not password:
        password = getpass.getpass("Please enter password for user %s: " % username)
        LOG.info("Adding new password to keyring")
        keyring.set_password("StudDP", username, password)
    return password


def user_yes_no_query(question):
    print('%s [y/n]' % question)
    while True:
        try:
            return strtobool(input().lower())
        except ValueError:
            sys.stdout.write('Please respond with \'y\' or \'n\'.\n')


def setup_logging(log_to_stdout):
    """
    Sets up the loggin handlers.
    """
    os.makedirs(LOG_PATH, exist_ok=True)
    file_handler_info = logging.FileHandler(os.path.join(LOG_PATH, 'info.log'))
    file_handler_info.setLevel(logging.INFO)
    file_handler_info.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    LOG.addHandler(file_handler_info)
    if log_to_stdout:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
        LOG.addHandler(ch)
    LOG.setLevel(logging.INFO)
    LOG.info('Logging initialized.')


def exit_func(*args):
    """
    Ensures clean exit by writing the current configuration file and
    deleting the pid file.
    """
    LOG.info('Invoking exit.')
    with open(CONFIG_FILE, 'w') as wfile:
        LOG.info('Writing config.')
        json.dump(CONFIG, wfile, sort_keys=True, indent=4 * ' ')
    os.unlink(PID_FILE)
    LOG.info('Exiting.')
    exit(0)

def parse_args():
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config",
                      action="store_true", dest="regenerate", default=False,
                      help="regenerate config file")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="log_to_stdout", default=False,
                      help="print log to stdout")
    parser.add_option("-n", "--noloop",
                      action="store_true", dest="noloop", default=False,
                      help="exit after one run")
    parser.add_option("-w", "--windows",
                      action="store_true", dest="on_windows", default=False,
                      help="remove characters that are forbidden in windows paths")
    parser.add_option("-u", "--update",
                      action="store_true", dest="update", default=False,
                      help="update files when they are updated on StudIP")
    return parser.parse_args()

if __name__ == "__main__":
    (options, args) = parse_args()

    setup_logging(options.log_to_stdout)

    if not os.path.exists(CONFIG_FILE):
        LOG.error('No %0s found. Please copy default_%0s to %0s and adjust it. Exiting.',
                  *([CONFIG_FILE]*3))
        exit(1)

    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, exit_func)

    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    with open(PID_FILE, 'w') as pid_file:
        pid_file.write(str(os.getpid()))

    with open(CONFIG_FILE, 'r') as rfile:
        CONFIG = json.load(rfile)

    if options.regenerate:
        CONFIG["courses_selected"] = False
        CONFIG["skip_courses"] = []

    StudDP(CONFIG, options.noloop, options.on_windows, options.update)()
