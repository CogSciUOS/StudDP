from .config import configuration as c
from .model import APIClient
import sys
from os.path import expanduser, join
import optparse
from pidfile import PidFile
import daemon
import time
import logging

log = logging.getLogger(__name__)

PID_FILE = expanduser(join('~', '.studdp', 'studdp.pid'))


def _parse_args():
    parser = optparse.OptionParser()
    parser.add_option("-s", "--select",
                      action="store_true", dest="select", default=False,
                      help="change course selection")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="log_to_stdout", default=False,
                      help="print log to stdout")
    parser.add_option("-d", "--daemonize",
                      action="store_true", dest="daemonize", default=False,
                      help="start as daemon. Use stopDP to end thread.")
    parser.add_option("-f", "--force",
                      action="store_true", dest="update_courses", default=False,
                      help="overwrite local changes")
    return parser.parse_args()


class _MainLoop:

    def __init__(self, daemonize, overwrite):
        self.daemonize = daemonize
        self.overwrite = overwrite

    def __call__(self):

        while True:
            courses = APIClient.get_courses()

            for course in courses:
                if not c.is_selected(course):
                    log.info("Skipping files for %s" % course)
                    continue
                for document in course.deep_documents:
                    document.download(self.overwrite)

            c.update_time()
            if not self.daemonize:
                return
            time.sleep(c.config["interval"])


def main():

    (options, args) = _parse_args()

    if options.log_to_stdout:
        root_logger = logging.getLogger("studdp")
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter(
            '%(name)s - %(levelname)s - %(message)s'))
        root_logger.handlers = [handler]

    if options.select:
        courses = APIClient.get_courses()
        c.selection_dialog(courses)
        sys.exit(0)

    task = _MainLoop(options.daemonize, options.update_courses)

    if options.daemonize:
        with daemon.DaemonContext(pidfile=PidFile(PID_FILE)):
            task()
    else:
        task()


if __name__ == "__main__":
    main()
