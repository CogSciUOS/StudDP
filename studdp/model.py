from os.path import join
from .config import configuration as c
from json import JSONDecodeError
import logging
import json
import requests as r
import shutil
import os
from memorised.decorators import memorise

log = logging.getLogger(__name__)


class BaseNode:
    def __init__(self, parent, title, object_id):
        self.id = str(object_id) if object_id is not None else None
        self._title = title
        self.parent = parent

    def __str__(self):
        return self.title

    @property
    def course(self):
        course = self.parent
        while course.parent:
            course = course.parent
        return course

    @property
    def path(self):
        if self.parent is None:
            return self.title
        return join(self.parent.path, self.title)

    @property
    def title(self):
        return c.namemap_lookup(self.id) if c.namemap_lookup(self.id) is not None else self._title


class Folder(BaseNode):
    @classmethod
    def from_response(cls, http_response, parent):
        return cls(parent, http_response["name"], http_response["folder_id"])

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


class Course(Folder):
    def __init__(self, title, course_id, semester_id):
        super().__init__(None, title, course_id)
        self.semester = semester_id

    @property
    def title(self):
        name = c.namemap_lookup(self.id)
        if name is None:
            name = self._title + " " + APIClient.get_semester_title(self)
            c.namemap_set(self.id, name)
        return name

    @property
    def course(self):
        return self

    @classmethod
    def from_response(cls, http_response, parent=None):
        return cls(http_response["title"], http_response["course_id"], http_response["semester_id"])


class Document(BaseNode):
    def __init__(self, parent, title, object_id, chtime):
        super().__init__(parent, title, object_id)
        self.chtime = chtime

    @classmethod
    def from_response(cls, http_response, parent):
        return cls(parent, http_response["filename"], http_response["document_id"], int(http_response["chdate"]))

    def download(self, overwrite=True):
        APIClient.download_document(self, overwrite)

    @property
    def path(self):
        return self.parent.path


class _APIClient:
    def __init__(self):
        pass

    @staticmethod
    def _url(route):
        return "%s%s" % (c.config['base_address'], route)

    def _get(self, route, stream=False):
        log.debug("Running GET request against %s" % route)
        return r.get(self._url(route), auth=c.auth, stream=stream)

    def get_contents(self, folder: Folder):
        log.debug("Listing Contents of %s/%s" % (folder.course.id, folder.id))
        if isinstance(folder, Course):
            try:  # Workaround for Ensemble Methods :)
                response = json.loads(self._get('/api/documents/%s/folder' % folder.course.id).text)
            except JSONDecodeError:
                log.error('Getting files for %s failed' % folder)
                return []
        else:
            response = json.loads(self._get('/api/documents/%s/folder/%s' % (folder.course.id, folder.id)).text)
            log.debug("Got response: %s" % response)

        documents = [Document.from_response(response, folder) for response in response["documents"]]

        folders = [Folder.from_response(response, folder) for response in response["folders"]]

        return documents + folders

    @staticmethod
    def modified(document: Document):
        return int(document.chtime) > c.config["last_check"]

    def download_document(self, document: Document, overwrite=True):
        path = os.path.join(os.path.expanduser(c.config["base_path"]), document.path)
        if not overwrite and os.path.exists(join(path, document.title)) and not self.modified(document):
            return
        log.info("Downloading %s" % join(path, document.title))
        file = self._get('/api/documents/%s/download' % document.id, stream=True)
        os.makedirs(path, exist_ok=True)
        with open(join(path, document.title), 'wb') as f:
            shutil.copyfileobj(file.raw, f)

    def get_semester_title(self, node: BaseNode):
        log.debug("Getting Semester Title for %s" % node.course.id)
        return self._get_semester_from_id(node.course.semester)

    @memorise()
    def _get_semester_from_id(self, semester_id):
        return self._get("/api/semesters/%s" % semester_id).json()["semester"]["title"]

    def get_courses(self):
        log.info("Listing Courses...")
        courses = json.loads(self._get('/api/courses').text)["courses"]
        courses = [Course.from_response(course) for course in courses]
        log.debug("Courses: %s" % [str(entry) for entry in courses])
        return courses

APIClient = _APIClient()



