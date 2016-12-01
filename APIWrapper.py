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
import atexit
from picker import Picker
import time

LOG = logging.getLogger(__name__)
out = logging.StreamHandler(sys.stdout)
out.setLevel(logging.INFO)
out.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
LOG.addHandler(out)
LOG.setLevel(logging.ERROR)

class APIWrapper(object):
    """
    An API wrapper for the Stud.IP Rest.API.
    See studip.github.io/studip-rest.ip/ for details.
    """

    def __init__(self, auth=("mschuwalow", "whiteglint01"),
                 base_address="https://studip.uos.de/plugins.php/restipplugin",
                 local_path="/tmp"):

        self._auth = auth
        self._base_address = base_address
        self.local_path = os.path.expanduser(local_path)

    def _url(self, route):
        """
        Creates an URL from the configuration and the route.
        """
        return "%s%s" % (self._base_address, route)

    def _get(self, route, stream=False):
        """
        Performs a GET request with the authentication from the configuration.
        Will raise errors that have to be handled by the user.
        """
        try:
            return requests.get(self._url(route), auth=self._auth, stream=False)
        except (TimeoutError,
                requests.packages.urllib3.exceptions.NewConnectionError,
                requests.packages.urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError) as error:
            LOG.error("Error on get %s: %s", route, error)
            return

    def get_courses(self):
        """
        Gets a list of courses.
        Return an empty list on errors.
        """
        while True:
            try:
                return json.loads(self._get('/api/courses').text)["courses"]
            except (ValueError, AttributeError, TimeoutError):
                LOG.error("Getting courses failed. Will retry")

    def get_course_folders(self, course):
        """
        Gets a list of document folders for a given course.
        Returns an empty list on errors.
        """
        while True:
            try:
                return json.loads(
                    self._get('/api/documents/%s/folder' % course['course_id']).text
                    )['folders']
            except (ValueError, AttributeError, TimeoutError):
                LOG.error("Getting course folders for %s failed. Will retry" % course["title"])
                LOG.info("StudIP is such quality content.")

    def get_documents(self, course):
        """
        Gets a list of documents and folders inside a folder.
        """
        documents = []
        folders = self.get_course_folders(course)
        for i, folder in enumerate(folders):
            folders[i]['path'] = os.path.join(self.local_path, course['title'])

        while folders:
            folder = folders.pop()
            while(True):
                try:
                    path = '/api/documents/%s/folder/%s' \
                            % (course['course_id'], folder['folder_id'])
                    response = self._get(path)
                    temp = json.loads(response.text)
                    break
                except (ValueError, AttributeError):
                    LOG.error('Error on loading %s. Will retry.' % path)

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
        shutil.copyfileobj(self._get('/api/documents/%s/download' % document['document_id'], stream=True).raw, docfile)
