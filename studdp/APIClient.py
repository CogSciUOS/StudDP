from .config import configuration as c
import requests as r
import os
import shutil
import json


class APIClient:

    def __init__(self):
        pass

    def _url(self, route):
        """
        Creates an URL from the configuration and the route.
        """
        return "%s%s" % (c.base_address, route)

    def get(self, route, stream=False):
        """
        
        :param route: 
        :param stream: 
        :return: 
        """
        return r.get(self._url(route), auth=c.auth, stream=stream)

    def get_courses(self):
        """
        :return: List of course objects for user
        """
        return json.loads(self.get('/api/courses').text)["courses"]

    def get_contents(self, course_id, item_id=None):
        if item_id is None:
            return json.loads(self.get('/api/documents/%s/folder' % course_id).text)
        else:
            return json.loads(self.get('/api/documents/%s/folder/%s' % (course_id, item_id)).text)

    def download_document(self, document_id, path):
        file = self.get('/api/documents/%s/download' % document_id, stream=True)
        os.makedirs(path, exist_ok=True)
        with open(path, 'wb') as f:
            shutil.copyfileobj(file.raw, f)

    def get_semester_title(self, course_id):
        semester_id = self.get("/api/courses/%s" % course_id).json()["course"]["semester_id"]
        return self.get("/api/semesters/%s" % semester_id).json()["semester"]["title"]








