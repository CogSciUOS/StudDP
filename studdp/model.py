"""
Collection of classes that represent the internal structure of Stud.ip.
The logical hierarchy is:

                    Course(root)
                    /  \\
                   /    \\
                  /      \\
               Folder    Document(leaf)
                /
               /
              /
        Document(leaf)

This module also contains the client for the stud.ip rest api as it is closely connected to the nodes on an implementation layer.
"""

import os
from os.path import join
import logging
import json
import shutil
import requests as r
from memorised.decorators import memorise
from werkzeug.utils import secure_filename
from .config import Config

c = Config()
log = logging.getLogger(__name__)


class BaseNode:
    """
    Base for all other nodes used here. Should normally not be used directly
    """
    def __init__(self, parent, title, object_id):
        self.id = str(object_id) if object_id is not None else None
        self._title = title
        self.parent = parent

    def __str__(self):
        return self.title

    @property
    def course(self):
        """
        Course this node belongs to
        """
        course = self.parent
        while course.parent:
            course = course.parent
        return course

    @property
    def path(self):
        """
        Path of this node on Studip. Looks like Coures/folder/folder/document. Respects the renaming policies defined in the namemap
        """
        if self.parent is None:
            return self.title
        return join(self.parent.path, self.title)

    @property
    def title(self):
        """
        get title of this node. If an entry for this course is found in the configuration namemap it is used, otherwise the default
        value from stud.ip is used.
        """
        tmp = c.namemap_lookup(self.id) if c.namemap_lookup(self.id) is not None else self._title
        return secure_filename(tmp)


class Folder(BaseNode):
    """
    Folder class that basically extends the basenode with the concept of contents(children) and a function that allows to get all children recursively.
    Also includes a parser to generate an instance from a typical studip response
    """
    @classmethod
    def from_response(cls, http_response, parent):
        return cls(parent, http_response["name"], http_response["folder_id"])

    @property
    def contents(self):
        """
        list of all children of this node. Documents are listed before the folders but there is no order inside that groups.
        """
        return client.get_contents(self)

    @property
    def deep_documents(self):
        """
        list of all documents find in subtrees of this node
        """
        tree = []
        for entry in self.contents:
            if isinstance(entry, Document):
                tree.append(entry)
            else:
                tree += entry.deep_documents
        return tree


class Course(Folder):
    """
    special folder representing courses(root nodes). Main difference lies in the automatic generation from responses and the default naming convention.
    If no name is found for courses the program defaults to $STUDIP_COURSE_NAME suffixed with the semester of the course. This prevents duplicates
    if one subscribes to a course over multiple semesters.
    """
    def __init__(self, title, course_id, semester_id):
        super().__init__(None, title, course_id)
        self.semester = semester_id

    @property
    def title(self):
        """
        The title of the course. If no entry in the namemap of the configuration is found a new entry is created with name=$STUD.IP_NAME + $SEMESTER_NAME
        """
        name = c.namemap_lookup(self.id)
        if name is None:
            name = self._title + " " + client.get_semester_title(self)
            c.namemap_set(self.id, name)
        return secure_filename(name)

    @property
    def course(self):
        return self

    @classmethod
    def from_response(cls, http_response, parent=None):
        return cls(http_response["title"], http_response["course_id"], http_response["semester_id"])


class Document(BaseNode):
    """
    Node representing a Document(leaf). Notable properties are a different format of responses and an option to download.
    """
    def __init__(self, parent, title, object_id, chtime):
        super().__init__(parent, title, object_id)
        self.chtime = chtime

    @classmethod
    def from_response(cls, http_response, parent):
        return cls(parent, http_response["filename"], http_response["document_id"], int(http_response["chdate"]))

    def download(self, overwrite=True):
        client.download_document(self, overwrite)

    @property
    def path(self):
        return self.parent.path


class _APIClient:
    """
    client for the studip rest api. Instances should not be generated manually but instead the instance available in this module should
    be used.
    """
    def __init__(self):
        pass

    @staticmethod
    def _url(route):
        """
        combine the baseurl from the configuration with a route in order to create a fully qualified url.
        """
        return "%s%s" % (c['base_address'], route)

    def _get(self, route, stream=False):
        """
        run a get request against an url. Returns the response which can optionally be streamed
        """
        log.debug("Running GET request against %s" % route)
        return r.get(self._url(route), auth=c.auth, stream=stream)

    def get_contents(self, folder: Folder):
        """
        List all contents of a folder. Returns a list of all Documents and Folders (in this order) in the folder.
        """
        log.debug("Listing Contents of %s/%s" % (folder.course.id, folder.id))
        if isinstance(folder, Course):
            response = json.loads(self._get('/api/documents/%s/folder' % folder.course.id).text)
        else:
            response = json.loads(self._get('/api/documents/%s/folder/%s' % (folder.course.id, folder.id)).text)
            log.debug("Got response: %s" % response)

        documents = [Document.from_response(response, folder) for response in response["documents"]]

        folders = [Folder.from_response(response, folder) for response in response["folders"]]

        return documents + folders

    @staticmethod
    def modified(document: Document):
        return int(document.chtime) > c["last_check"]

    def download_document(self, document: Document, overwrite=True, path=None):
        """
        Download a document to the given path. if no path is provided the path is constructed frome the base_url + stud.ip path + filename.
        If overwrite is set the local version will be overwritten if the file was changed on studip since the last check
        """
        if not path:
            path = os.path.join(os.path.expanduser(c["base_path"]), document.path)
        if (self.modified(document) and overwrite) or not os.path.exists(join(path, document.title)):
            log.info("Downloading %s" % join(path, document.title))
            file = self._get('/api/documents/%s/download' % document.id, stream=True)
            os.makedirs(path, exist_ok=True)
            with open(join(path, document.title), 'wb') as f:
                shutil.copyfileobj(file.raw, f)

    def get_semester_title(self, node: BaseNode):
        """
        get the semester of a node
        """
        log.debug("Getting Semester Title for %s" % node.course.id)
        return self._get_semester_from_id(node.course.semester)

    @memorise()
    def _get_semester_from_id(self, semester_id):
        return self._get("/api/semesters/%s" % semester_id).json()["semester"]["title"]

    def get_courses(self):
        """
        use the base_url and auth data from the configuration to list all courses the user is subscribed to
        """
        log.info("Listing Courses...")
        courses = json.loads(self._get('/api/courses').text)["courses"]
        courses = [Course.from_response(course) for course in courses]
        log.debug("Courses: %s" % [str(entry) for entry in courses])
        return courses

client = _APIClient()
