import logging.config
from logging import NullHandler
from os.path import expanduser, join, dirname
from os import makedirs

logging.getLogger(__name__).addHandler(NullHandler())
LOG_PATH = expanduser(join('~', '.studdp', 'studdp.log'))
makedirs(dirname(LOG_PATH), exist_ok=True)

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'minimal': {
            'format': '[%(levelname)s]: %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'minimal'
        },
        'file_handler': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': LOG_PATH
        }
    },
    'loggers': {
        '': {
            'handlers': ['default', 'file_handler'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
})

logging.info("Logging initialized")
