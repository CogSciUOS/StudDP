from os.path import join
from .config import configuration as c
from json import JSONDecodeError
import logging
import json
import requests as r
import shutil
import os

log = logging.getLogger(__name__)


class _APIClient:
    def __init__(self):
        pass

    @staticmethod
    def _url(route):
        """
        Creates an URL from the configuration and the route.
        """
        return "%s%s" % (c.config['base_address'], route)

    def _get(self, route, stream=False):
        """

        :param route: 
        :param stream: 
        :return: 
        """
        log.debug("Running GET request against %s" % route)
        return r.get(self._url(route), auth=c.auth, stream=stream)

    def get_contents(self, folder):
        log.debug("Listing Contents of %s/%s" % (folder.course_id, folder.id))
        if folder.id is None:
            try: # Workaround for courses not having normal folders
                response = json.loads(self._get('/api/documents/%s/folder' % folder.course_id).text)
            except JSONDecodeError:
                log.error('Getting files for %s failed' % folder)
                return []
        else:
            response = json.loads(self._get('/api/documents/%s/folder/%s' % (folder.course_id, folder.id)).text)

        documents = list(map(lambda x: Document.from_response(x, folder.path, folder.course_id),
                             response["documents"]))

        folders = list(map(lambda x: Folder.from_response(x, folder.path, folder.course_id),
                           response["folders"]))

        return documents + folders

    @staticmethod
    def modified(document):
        """
        Checks if a document has been changed since last download.
        """
        return int(document.chtime) > c.config["last_check"]

    def download_document(self, document, overwrite=True):
        path = os.path.join(os.path.expanduser(c.config["base_path"]), document.path)
        if not overwrite and os.path.exists(path) and not self.modified(document):
            return
        log.info("Downloading %s" % join(path, document.title))
        file = self._get('/api/documents/%s/download' % document.id, stream=True)
        os.makedirs(path, exist_ok=True)
        with open(join(path, document.title), 'wb') as f:
            shutil.copyfileobj(file.raw, f)

    def get_semester_title(self, course):
        log.debug("Getting Semester Title for %s" % course.course_id)
        semester_id = self._get("/api/courses/%s" % course.course_id).json()["course"]["semester_id"]
        return self._get("/api/semesters/%s" % semester_id).json()["semester"]["title"]

    def get_courses(self):
        """
        :return: List of course objects for user
        """
        log.info("Listing Courses...")
        courses = json.loads(self._get('/api/courses').text)["courses"]
        courses = [Folder.from_response_course(course) for course in courses]
        log.debug("Courselist: %s" % [str(entry) for entry in courses])
        return courses

APIClient = _APIClient()


class BaseNode:

    def __init__(self, path, title, course_id, object_id, chtime):
        self._path = path
        self.id = str(object_id) if object_id is not None else None
        self.course_id = str(course_id) if course_id is not None else None
        self._title = title
        self.chtime = chtime

    def __str__(self):
        return self.title

    @property
    def path(self):
        return join(self._path, self.title)

    @property
    def title(self):
        if self.id is not None:
            return c.namemap_lookup(self.id) if c.namemap_lookup(self.id) is not None else self._title
        # We are a course/root node
        name = c.namemap_lookup(self.course_id)
        if name is None:
            name = self._title + " " + APIClient.get_semester_title(self)
            c.namemap_set(self.course_id, name)
        return name


class Folder(BaseNode):

    @classmethod
    def from_response(cls, http_response, path, course_id):
        return cls(path, http_response["name"], course_id, http_response["folder_id"], int(http_response["chdate"]))

    @classmethod
    def from_response_course(cls, http_response):
        """
        The Response dict for a course object has to be treated differently
        :param http_response: 
        :return: 
        """
        return cls(".", http_response["title"], http_response["course_id"], None, int(http_response["chdate"]))

    @property
    def contents(self):
        return APIClient.get_contents(self)

    @property
    def deep_documents(self):
        tree = []
        for entry in self.contents:
            if isinstance(entry, Document):
                tree.append(entry)
            else:
                tree += entry.deep_documents
        return tree


class Document(BaseNode):
    @classmethod
    def from_response(cls, http_response, path, course_id):
        return cls(path, http_response["filename"], course_id, http_response["document_id"], int(http_response["chdate"]))

    def download(self, overwrite=True):
        APIClient.download_document(self, overwrite)

    @property
    def path(self):
        return self._path




