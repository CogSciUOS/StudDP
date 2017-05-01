from os.path import join
from .config import configuration as c
from .APIClient import APIClient as a


class BaseNode:
    def __init__(self, path, title, course_id, object_id):
        self._path = path
        self._id = object_id
        self._master = course_id
        self._title = title

    def __str__(self):
        return self.title

    @property
    def path(self):
        return join(self._path, self._title)

    @property
    def id(self):
        return self._id

    @property
    def course_id(self):
        return self._master

    @property
    def title(self):
        return c.namemap.lookup(self.id) if c.namemap.lookup(self.id) is not None else self._title


class Folder(BaseNode):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        files = a().get_contents(self.course_id, self.id)
        self._folders = list(map(lambda x: Folder.from_response(x, self.path, self.course_id),
                                 files["folders"]))
        self._documents = list(map(lambda x: Document.from_response(x, self.path, self.course_id),
                                   files["documents"]))

    @classmethod
    def from_response(cls, http_response, path, course_id):
        return cls(path, http_response["name"], course_id, http_response["folder_id"])

    @classmethod
    def from_response_course(cls, http_response):
        """
        The Response dict for a course object has to be treated differently
        :param http_response: 
        :return: 
        """
        return cls(http_response["title"], http_response["title"], http_response["course_id"], None)

    @property
    def folders(self):
        return self._folders

    @property
    def documents(self):
        return self._documents

    @property
    def deep_documents(self):
        tree = []
        for folder in self.folders:
            tree += folder.deep_documents
        return self.documents + tree

    @property
    def title(self):
        if self.id is not None:
            return super().title
        # We are a course/root node
        name = c.namemap.lookup(self.course_id)
        if name is None:
            name = self._title + " " + a().get_semester_title(self.course_id)
            c.namemap.set(self.course_id, name)
        return name


class Document(BaseNode):
    @classmethod
    def from_response(cls, http_response, path, course_id):
        return cls(path, http_response["name"], course_id, http_response["document_id"])

