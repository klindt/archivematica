#!/usr/bin/python2 -OO

import logging
from logging.handlers import RotatingFileHandler
import os
import sys

logger = logging.getLogger('archivematica.mcp.client')
logger.addHandler(RotatingFileHandler("/var/log/archivematica/archivematica.log", maxBytes=4194304),
    level=logging.INFO)

# Set up Django settings
path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

path = "/usr/lib/archivematica/archivematicaCommon"
if path not in sys.path:
    sys.path.append(path)
import storageService as storage_service


def get_aip_storage_locations():
    """ Return a dict of AIP Storage Locations and their descriptions."""
    storage_directories = storage_service.get_location(purpose="AS")
    logging.debug("Storage Directories: {}".format(storage_directories))
    choices = {}
    for storage_dir in storage_directories:
        choices[storage_dir['description']] = storage_dir['resource_uri']
    print choices


if __name__ == '__main__':
    get_aip_storage_locations()
