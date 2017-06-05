StudDP
======

StudDP is a file downloader for `Stud.IP <http://studip.de/>`__. It uses
the `Stud.IP: Rest.IP <http://studip.github.io/studip-rest.ip/>`__
plugin to download files when they changed or are not existent on the
file system.

Setup
-----

To set it up, do the following:

Install via pip:

.. code:: sh

    pip install StudDP

or alternatively:

.. code:: sh

    git clone https://github.com/shoeffner/StudDP
    cd StudDP
    pip install -r requirements.txt

Note: If you install manually you will have to run the included scripts
as:

.. code:: sh

    python -m studdp.studdp

Modify the config.yml:
~~~~~~~~~~~~~~~~~~~~~~~

# The base address of your universities stud.ip deployment. Change this if you don't study in Osnabrueck
base_address: 'https://studip.uos.de/plugins.php/restipplugin'

# The path to use as the root of the studdp downloads. The program will rebuild the course-structure of stud.ip under this root.
base_path: '~/studip'

# How often to check in seconds. This option is only respected when run as a daemon.
interval: 1200

# Your stud.ip username
username: 'ChangeMe!'

# Your stud.ip username is either stored in your keyring or read from this file if use_keyring is set to false.
use_keyring: true
password: 'optional' # only respected if use_keyring is false

# Your selected courses. You should not change this directly but rather use studdp -c to configure them
selected_courses:
- '_course_id'

# All stud.ip nodes found here will be renamed as desired. By default one entry is created for every course in order to
# include the semester in the name. This works the same way for folders and documents. The ids can for example be
# easily found on studip using a browser.
namemap:
'_course': '_title' # this is the format you should use. isn't yaml beautiful?

# Time of last check. You should normally not touch this
last_check: 0

Run
---

When running for the first time, use:

.. code:: sh

    studdp

To get information about options, use:

.. code:: sh

    Usage: studdp [options]

    Options:
    -h, --help       show this help message and exit
    -c, --config     change course selection
    -s, --stop       stop the daemon process
    -d, --daemonize  start as daemon. Use studdp -s to stop daemon.
    -f, --force      overwrite local changes
    --password       change the password entry in the keyring


When running it for the first time, it should prompt you for your StudIP
password. It will then be stored in your login keyring. This of course
requires a keyring like the gnome keyring installed. If you prefer your
password saved in cleartext in some config file, you can set use_keyring
to false in the config and provide your password there.

Select courses
___

By default studdp will download all courses you are subscribed to to the folder
defined in base_path. You can limit this selection using studdp -c which will bring
up a ncurses interface to configure your course selection.

.. figure:: https://cdn.rawgit.com/shoeffner/StudDP/develop/screenshots/courses.png
   :alt: 

You can later use the --password and -c options to reconfigure your password and
courses respectively.

Running as a daemon
-------------------

To run it as a daemon, use:

.. code:: sh

    studdp -d

To stop it the daemon, use:

.. code:: sh

    studdp -s

Other information
-----------------

To view the log use:

.. code:: sh

    tail -f ~/.studdp/info.log

To uninstall use:

.. code:: sh

    rm -rf StudDP
    rm -rf ~/.studdp

or if installed via pip:
.. code:: sh
    pip uninstall StudDP
