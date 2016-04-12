#!/usr/bin/env python3.5

"""
StudDP downloads files from Stud.IP.
"""

import json
import os
import shutil
import time

import requests

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

class APIWrapper(object):
    """
    An API wrapper for the Stud.IP Rest.API.
    See studip.github.io/studip-rest.ip/ for details.
    """

    def __init__(self, configuration):
        """
        Initializes the API's auth and base address.
        """
        self.__auth = (configuration['username'], configuration['password'])
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
        return requests.get(self.__url__(route), auth=self.__auth, stream=stream)

    def get_courses(self):
        """
        Gets a list of courses.
        """
        return json.loads(self.__get('/api/courses').text)['courses']

    def __get_course_folders(self, course):
        """
        Gets a list of document folders for a given course id.
        """
        try:
            return json.loads(
                self.__get('/api/documents/{}/folder'.format(course['course_id'])).text
                )['folders']
        except ValueError:
            return []

    def get_documents(self, course):
        """
        Gets a list of documents and folders inside a folder.
        """
        documents = []
        folders = self.__get_course_folders(course)
        for i, folder in enumerate(folders):
            folders[i]['path'] = os.path.join(self.__local_path, course['title'])

        while folders:
            folder = folders.pop()
            temp = json.loads(
                self.__get('/api/documents/{}/folder/{}'
                           .format(course['course_id'], folder['folder_id'])
                          ).text
                )
            for key in ['folders', 'documents']:
                for i in range(len(temp[key])):
                    temp[key][i]['path'] = os.path.join(folder['path'], folder['name'])
            documents += temp['documents']
            folders += temp['folders']
        return documents

    def download_document(self, document, docfile):
        """
        Downloads the document to docfile.
        """
        shutil.copyfileobj(self.__get('/api/documents/{}/download'.format(document['document_id']),
                                      stream=True).raw, docfile)

class StudDP(object):
    """
    The main program loops until interrupted.
    Every time files were changed after the last check, they are downloaded.
    Files are also downloaded if they do not exist locally.
    """

    def __init__(self, config):
        """
        Initializes the API and the update frequencies.
        """
        self.last_check = config['last_check']
        self.interval = config['interval']
        self.api = APIWrapper(config)

    def __needs_download(self, document):
        """
        Checks if a download of the document is needed.
        """
        return int(document['chdate']) > self.last_check or \
               not os.path.exists(os.path.join(document['path'], document['filename']))

    def __call__(self):
        """
        Starts the main loop and checks periodically for document changes and downloads.
        """
        while True:
            for course in self.api.get_courses():
                documents = self.api.get_documents(course)
                for document in documents:
                    if self.__needs_download(document):
                        path = os.path.join(document['path'], document['filename'])
                        print('Downloading {}...'.format(path))
                        os.makedirs(document['path'], exist_ok=True)
                        with open(path, 'wb') as docfile:
                            self.api.download_document(document, docfile)
                        print('Downloaded {}.'.format(path))
            self.last_check = time.time()
            time.sleep(self.interval)

    def get_interval(self):
        """
        Returns the interval.
        """
        return self.interval

    def get_last_check(self):
        """
        Returns the last check.
        """
        return self.last_check

if __name__ == "__main__":
    if not os.path.exists(CONFIG_FILE):
        print('No {0} found. Please copy default_{0} to {0} and adjust it. Exiting.'
              .format(CONFIG_FILE))
        exit(1)

    with open(CONFIG_FILE, 'r') as configfile:
        CONFIG = json.load(configfile)

    STUDDP = StudDP(CONFIG)
    try:
        STUDDP()
    except KeyboardInterrupt:
        CONFIG['last_check'] = STUDDP.get_last_check()
        with open(CONFIG_FILE, 'w') as configfile:
            json.dump(CONFIG, configfile)

