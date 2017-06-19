"""
Main Loop that runs as a daemon and takes care of only downloading selected courses, etc.
"""
import sys
from os.path import expanduser, join
import os
import optparse
import daemon
from daemon.pidfile import PIDLockFile
import time
import logging
from .model import client
from .config import Config
from . import LOG_PATH

c = Config()
log = logging.getLogger(__name__)

PID_FILE = expanduser(join('~', '.studdp', 'studdp.pid'))


def _parse_args():
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config",
                      action="store_true", dest="select", default=False,
                      help="change course selection")
    parser.add_option("-s", "--stop",
                      action="store_true", dest="stop", default=False,
                      help="stop the daemon process")
    parser.add_option("-d", "--daemonize",
                      action="store_true", dest="daemonize", default=False,
                      help="start as daemon. Use studdp -s to stop daemon.")
    parser.add_option("-f", "--force",
                      action="store_true", dest="update_courses", default=False,
                      help="overwrite local changes")
    parser.add_option("--password",
                      action="store_true", dest="change_password", default=False,
                      help="change the password entry in the keyring")
    return parser.parse_args()


class _MainLoop:
    """
    Main Loop that takes care of checking whether courses need to be downloaded and takes care of general task orchestration.
    """

    def __init__(self, daemonize, overwrite):
        self.daemonize = daemonize
        self.overwrite = overwrite

    def __call__(self):
        while True:
            courses = client.get_courses()

            for course in courses:
                if not c.is_selected(course):
                    log.debug("Skipping files for %s" % course)
                    continue
                log.info("Checking files for %s..." % course)
                for document in course.deep_documents:
                    document.download(self.overwrite)

            c.update_time()
            log.info("Finished checking.")
            if not self.daemonize:
                return
            log.info("Going to sleep for %d" % c["interval"])
            time.sleep(c["interval"])


def main():
    """
    parse command line options and either launch some configuration dialog or start an instance of _MainLoop as a daemon
    """
    (options, _) = _parse_args()

    if options.change_password:
        c.keyring_set_password(c["username"])
        sys.exit(0)

    if options.select:
        courses = client.get_courses()
        c.selection_dialog(courses)
        c.save()
        sys.exit(0)

    if options.stop:
        os.system("kill -2 `cat ~/.studdp/studdp.pid`")
        sys.exit(0)

    task = _MainLoop(options.daemonize, options.update_courses)

    if options.daemonize:
        log.info("daemonizing...")
        with daemon.DaemonContext(working_directory=".", pidfile=PIDLockFile(PID_FILE)):
            # we have to create a new logger in the daemon context
            handler = logging.FileHandler(LOG_PATH)
            handler.setFormatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            log.addHandler(handler)
            task()
    else:
        task()


if __name__ == "__main__":
    main()
