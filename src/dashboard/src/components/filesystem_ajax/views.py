# This file is part of Archivematica.
#
# Copyright 2010-2013 Artefactual Systems Inc. <http://artefactual.com>
#
# Archivematica is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Archivematica is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Archivematica.  If not, see <http://www.gnu.org/licenses/>.

import base64
import os
import logging
import shutil
import sys
import tempfile
import uuid

from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.db import connection

from components import helpers
import components.ingest.helpers as ingest_helpers
import components.filesystem_ajax.helpers as filesystem_ajax_helpers
from main import models

sys.path.append("/usr/lib/archivematica/archivematicaCommon")
import archivematicaFunctions
import databaseFunctions
import elasticSearchFunctions
from archivematicaCreateStructuredDirectory import createStructuredDirectory
import storageService as storage_service

# for unciode sorting support
import locale
locale.setlocale(locale.LC_ALL, '')

logger = logging.getLogger(__name__)
logging.basicConfig(filename="/tmp/archivematicaDashboard.log",
    level=logging.INFO)

SHARED_DIRECTORY_ROOT   = '/var/archivematica/sharedDirectory'
ACTIVE_TRANSFER_DIR     = SHARED_DIRECTORY_ROOT + '/watchedDirectories/activeTransfers'
STANDARD_TRANSFER_DIR   = ACTIVE_TRANSFER_DIR + '/standardTransfer'
ORIGINAL_DIR            = SHARED_DIRECTORY_ROOT + '/www/AIPsStore/transferBacklog/originals'

DEFAULT_ARRANGE_PATH = '/arrange/'


def directory_children_proxy_to_storage_server(request, location_uuid, basePath=False):
    path = ''
    if (basePath):
        path = base64.b64decode(basePath)
    path = path + base64.b64decode(request.GET.get('base_path', ''))
    path = path + base64.b64decode(request.GET.get('path', ''))
    path = base64.b64encode(path)

    response = storage_service.browse_location(location_uuid, path)

    return helpers.json_response(response)

def contents(request):
    path = request.GET.get('path', '/home')
    response = filesystem_ajax_helpers.directory_to_dict(path)
    return helpers.json_response(response)

def arrange_contents(request):
    base_path = request.GET.get('path', DEFAULT_ARRANGE_PATH)

    # Must indicate that base_path is a folder by ending with /
    if not base_path.endswith('/'):
        base_path += '/'

    if not base_path.startswith(DEFAULT_ARRANGE_PATH):
        base_path = DEFAULT_ARRANGE_PATH

    # Query SIP Arrangement for results
    # Get all the paths that are not in SIPs and start with base_path.  We don't
    # need the objects, just the arrange_path
    paths = models.SIPArrange.objects.filter(sip_created=False).filter(arrange_path__startswith=base_path).order_by('arrange_path').values_list('arrange_path', flat=True)

    # Convert the response into an entries [] and directories []
    # 'entries' contains everything (files and directories)
    response = {'entries': [], 'directories': []}
    for path in paths:
        # Stip common prefix
        if path.startswith(base_path):
            path = path[len(base_path):]
        entry = path.split('/', 1)[0]
        # Only insert once
        if entry and entry not in response['entries']:
            response['entries'].append(entry)
            if path.endswith('/'):  # path is a dir
                response['directories'].append(entry)

    return helpers.json_response(response)


def originals_contents(request):
    path = request.GET.get('path', 'originals').lstrip('/')
    # IDEA memoize the backlog location?
    backlog = storage_service.get_location(purpose='BL')[0]

    # TODO need to be able to search on accession ID
    response = storage_service.browse_location(backlog['uuid'], path)

    return helpers.json_response(response)

def delete(request):
    filepath = request.POST.get('filepath', '')
    filepath = os.path.join('/', filepath)
    error = filesystem_ajax_helpers.check_filepath_exists(filepath)

    if error == None:
        filepath = os.path.join(filepath)
        if os.path.isdir(filepath):
            try:
                shutil.rmtree(filepath)
            except:
                error = 'Error attempting to delete directory.'
        else:
            os.remove(filepath)

    response = {}

    # if deleting from originals, delete ES data as well
    if ORIGINAL_DIR in filepath and filepath.index(ORIGINAL_DIR) == 0:
        transfer_uuid = _find_uuid_of_transfer_in_originals_directory_using_path(filepath)
        if transfer_uuid != None:
            elasticSearchFunctions.connect_and_remove_backlog_transfer_files(transfer_uuid)

    if error != None:
      response['message'] = error
      response['error']   = True
    else:
      response['message'] = 'Delete successful.'

    return helpers.json_response(response)

def get_temp_directory(request):
    temp_base_dir = helpers.get_client_config_value('temp_dir')

    response = {}

    # use system temp dir if none specifically defined
    if temp_base_dir == '':
        temp_dir = tempfile.mkdtemp()
    else:
        try:
            temp_dir = tempfile.mkdtemp(dir=temp_base_dir)
        except:
            temp_dir = ''
            response['error'] = 'Unable to create temp directory.'

    #os.chmod(temp_dir, 0o777)

    response['tempDir'] = temp_dir

    return helpers.json_response(response)

def copy_transfer_component(request):
    transfer_name = archivematicaFunctions.unicodeToStr(request.POST.get('name', ''))
    # Note that the path may contain arbitrary, non-unicode characters,
    # and hence is POSTed to the server base64-encoded
    path = base64.b64decode(request.POST.get('path', ''))
    destination = archivematicaFunctions.unicodeToStr(request.POST.get('destination', ''))

    error = None

    if transfer_name == '':
        error = 'No transfer name provided.'
    else:
        if path == '':
            error = 'No path provided.'
        else:
            # if transfer compontent path leads to an archive, treat as zipped
            # bag
            if helpers.file_is_an_archive(path):
                filesystem_ajax_helpers.rsync_copy(path, destination)
                paths_copied = 1
            else:
                transfer_dir = os.path.join(destination, transfer_name)

                # Create directory before it is used, otherwise shutil.copy()
                # would that location to store a file
                if not os.path.isdir(transfer_dir):
                    os.mkdir(transfer_dir)

                paths_copied = 0

                # cycle through each path copying files/dirs inside it to transfer dir
                try:
                    entries = filesystem_ajax_helpers.sorted_directory_list(path)
                except os.error as e:
                    error = "Error: {e.strerror}: {e.filename}".format(e=e)
                    # Clean up temp dir - don't use os.removedirs because
                    # <shared_path>/tmp might not have anything else in it and
                    # we don't want to delete it
                    os.rmdir(transfer_dir)
                    os.rmdir(destination)
                else:
                    for entry in entries:
                        entry_path = os.path.join(path, entry)
                        filesystem_ajax_helpers.rsync_copy(entry_path, transfer_dir)
                        paths_copied = paths_copied + 1

    response = {}

    if error != None:
        response['message'] = error
        response['error']   = True
    else:
        response['message'] = 'Copied ' + str(paths_copied) + ' entries.'

    return helpers.json_response(response)

def copy_to_originals(request):
    filepath = request.POST.get('filepath', '')
    error = filesystem_ajax_helpers.check_filepath_exists('/' + filepath)

    if error == None:
        processingDirectory = '/var/archivematica/sharedDirectory/currentlyProcessing/'
        sipName = os.path.basename(filepath)
        autoProcessSIPDirectory = '/var/archivematica/sharedDirectory/watchedDirectories/SIPCreation/SIPsUnderConstruction/'
        tmpSIPDir = os.path.join(processingDirectory, sipName) + "/"
        destSIPDir =  os.path.join(autoProcessSIPDirectory, sipName) + "/"

        sipUUID = uuid.uuid4().__str__()

        createStructuredDirectory(tmpSIPDir)
        databaseFunctions.createSIP(destSIPDir.replace('/var/archivematica/sharedDirectory/', '%sharedPath%'), sipUUID)

        objectsDirectory = os.path.join('/', filepath, 'objects')

        #move the objects to the SIPDir
        for item in os.listdir(objectsDirectory):
            shutil.move(os.path.join(objectsDirectory, item), os.path.join(tmpSIPDir, "objects", item))

        #moveSIPTo autoProcessSIPDirectory
        shutil.move(tmpSIPDir, destSIPDir)

    response = {}

    if error != None:
        response['message'] = error
        response['error']   = True
    else:
        response['message'] = 'Copy successful.'

    return helpers.json_response(response)

def copy_to_start_transfer(request):
    filepath  = archivematicaFunctions.unicodeToStr(request.POST.get('filepath', ''))
    type      = request.POST.get('type', '')
    accession = request.POST.get('accession', '')

    error = filesystem_ajax_helpers.check_filepath_exists('/' + filepath)

    if error == None:
        # confine destination to subdir of originals
        filepath = os.path.join('/', filepath)
        basename = os.path.basename(filepath)

        # default to standard transfer
        type_paths = {
          'standard':     'standardTransfer',
          'unzipped bag': 'baggitDirectory',
          'zipped bag':   'baggitZippedDirectory',
          'dspace':       'Dspace',
          'maildir':      'maildir',
          'TRIM':         'TRIM'
        }

        try:
          type_subdir = type_paths[type]
          destination = os.path.join(ACTIVE_TRANSFER_DIR, type_subdir)
        except KeyError:
          destination = os.path.join(STANDARD_TRANSFER_DIR)

        # if transfer compontent path leads to a ZIP file, treat as zipped
        # bag
        if not helpers.file_is_an_archive(filepath):
            destination = os.path.join(destination, basename)
            destination = helpers.pad_destination_filepath_if_it_already_exists(destination)

        # relay accession via DB row that MCPClient scripts will use to get
        # supplementary info from
        if accession != '':
            temp_uuid = uuid.uuid4().__str__()
            mcp_destination = destination.replace(SHARED_DIRECTORY_ROOT + '/', '%sharedPath%') + '/'
            transfer = models.Transfer.objects.create(
                uuid=temp_uuid,
                accessionid=accession,
                currentlocation=mcp_destination
            )
            transfer.save()

        try:
            shutil.move(filepath, destination)
        except:
            error = 'Error copying from ' + filepath + ' to ' + destination + '. (' + str(sys.exc_info()[0]) + ')'

    response = {}

    if error != None:
        response['message'] = error
        response['error']   = True
    else:
        response['message'] = 'Copy successful.'

    return helpers.json_response(response)

def copy_from_arrange_to_completed(request):
    filepath = '/' + request.POST.get('filepath', '')

    if filepath != '':
        ingest_helpers.initiate_sip_from_files_structured_like_a_completed_transfer(filepath)

    #return copy_to_originals(request)

def create_directory_within_arrange(request):
    """ Creates a directory entry in the SIPArrange table.

    path: GET parameter, path to directory in DEFAULT_ARRANGE_PATH to create
    """
    error = None
    
    path = request.POST.get('path', '')

    if path:
        if path.startswith(DEFAULT_ARRANGE_PATH):
            models.SIPArrange.objects.create(
                original_path=None,
                arrange_path=os.path.join(path, ''), # ensure ends with /
                file_uuid=None,
            )
        else:
            error = 'Directory is not within the arrange directory.'

    if error is not None:
        response = {
            'message': error,
            'error': True,
        }
    else:
        response = {'message': 'Creation successful.'}

    return helpers.json_response(response)

def move_within_arrange(request):
    """ Move files/folders within SIP Arrange.

    source path is in GET parameter 'filepath'
    destination path is in GET parameter 'destination'.

    If a source/destination path ends with / it is assumed to be a folder,
    otherwise it is assumed to be a file.
    """
    sourcepath  = request.POST.get('filepath', '')
    destination = request.POST.get('destination', '')
    error = None

    logging.debug('Move within arrange: source: {}, destination: {}'.format(sourcepath, destination))

    if not (sourcepath.startswith(DEFAULT_ARRANGE_PATH) and destination.startswith(DEFAULT_ARRANGE_PATH)):
        error = '{} and {} must be inside {}'.format(sourcepath, destination, DEFAULT_ARRANGE_PATH)
    elif destination.endswith('/'):  # destination is a directory
        if sourcepath.endswith('/'):  # source is a directory
            folder_contents = models.SIPArrange.objects.filter(arrange_path__startswith=sourcepath)
            # Strip the last folder off sourcepath, but leave a trailing /, so
            # we retain the folder name when we move the files.
            source_parent = '/'.join(sourcepath.split('/')[:-2])+'/'
            for entry in folder_contents:
                entry.arrange_path = entry.arrange_path.replace(source_parent,destination,1)
                entry.save()
        else:  # source is a file
            models.SIPArrange.objects.filter(arrange_path=sourcepath).update(arrange_path=destination+os.path.basename(sourcepath))
    else:  # destination is a file (this should have been caught by JS)
        error = 'You cannot drag and drop onto a file.'

    if error is not None:
        response = {
            'message': error,
            'error': True,
        }
    else:
        response = {'message': 'SIP files successfully moved.'}

    return helpers.json_response(response)

def _find_uuid_of_transfer_in_originals_directory_using_path(transfer_path):
    transfer_basename = transfer_path.replace(ORIGINAL_DIR, '').split('/')[1]

    # use lookup path to cleanly find UUID
    lookup_path = '%sharedPath%www/AIPsStore/transferBacklog/originals/' + transfer_basename + '/'
    cursor = connection.cursor()
    sql = 'SELECT unitUUID FROM transfersAndSIPs WHERE currentLocation=%s LIMIT 1'
    cursor.execute(sql, (lookup_path, ))
    possible_uuid_data = cursor.fetchone()

    # if UUID valid in system found, remove it
    if possible_uuid_data:
        return possible_uuid_data[0]
    else:
        return None

def _arrange_dir():
    return os.path.realpath(os.path.join(
        helpers.get_client_config_value('sharedDirectoryMounted'),
        'arrange'))


def _get_arrange_directory_tree(backlog_uuid, original_path, arrange_path):
    """ Fetches all the children of original_path from backlog_uuid and creates
    an identical tree in arrange_path.

    Helper function for copy_to_arrange.
    """
    ret = []
    browse = storage_service.browse_location(backlog_uuid, original_path)

    # Add everything that is not a directory (ie that is a file)
    entries = [e for e in browse['entries'] if e not in browse['directories']]
    for entry in entries:
        if entry not in ('processingMCP.xml'):
            ret.append(
                {'original_path': os.path.join(original_path, entry),
                 'arrange_path': os.path.join(arrange_path, entry),
                  'file_uuid': 'TODO'})  # TODO how get file UUID?

    # Add directories and recurse, adding their children too
    for directory in browse['directories']:
        original_dir = os.path.join(original_path, directory, '')
        arrange_dir = os.path.join(arrange_path, directory, '')
        # Don't fetch metadata or logs dirs
        # TODO only filter if the children of a SIP ie /arrange/sipname/metadata
        if not directory in ('metadata', 'logs'):
            ret.append({'original_path': None,
                        'arrange_path': arrange_dir,
                        'file_uuid': None})
            ret.extend(_get_arrange_directory_tree(backlog_uuid, original_dir, arrange_dir))

    return ret


def copy_to_arrange(request):
    """ Add files from backlog to in-progress SIPs being arranged.

    sourcepath: GET parameter, path relative to this pipelines backlog. Leading
        '/'s are stripped
    destination: GET parameter, path within arrange folder, should start with
        DEFAULT_ARRANGE_PATH ('/arrange/')
    """
    error = None

    # Insert each file into the DB
    # Check if the file is already in the DB (original == DB.arrange) and update if so
    sourcepath  = request.POST.get('filepath', '').lstrip('/')
    destination = request.POST.get('destination', '')
    logging.info('copy_to_arrange: sourcepath: {}'.format(sourcepath))
    logging.info('copy_to_arrange: destination: {}'.format(destination))

    if not sourcepath or not destination:
        error = "GET parameter 'filepath' or 'destination' was blank."

    if not destination.startswith(DEFAULT_ARRANGE_PATH):
        error = '{} must be in arrange directory.'.format(destination)

    # If drop onto a file, drop it into its parent directory instead
    if not destination.endswith('/'):
        destination = os.path.dirname(destination)

    # Files cannot go into the top level folder
    if destination == DEFAULT_ARRANGE_PATH and not sourcepath.endswith('/'):
        error = '{} must go in a SIP, cannot be dropped onto {}'.format(
            sourcepath, DEFAULT_ARRANGE_PATH)

    # Construct the base arrange_path differently for files vs folders
    if sourcepath.endswith('/'):
        leaf_dir = sourcepath.split('/')[-2]
        arrange_path = os.path.join(destination, leaf_dir) + '/'
    else:
        arrange_path = os.path.join(destination, os.path.basename(sourcepath))
    logging.info('copy_to_arrange: arrange_path: {}'.format(arrange_path))

    # Cannot add an object that already exists
    if models.SIPArrange.objects.filter(arrange_path=arrange_path).exists():
        # TODO pad this with _, see helpers.pad_destination_filepath_if_it_already_exists
        error = '{} already exists.'.format(arrange_path)

    # Create new SIPArrange entry for each object being copied over
    if not error:
        # IDEA memoize the backlog location?
        backlog_uuid = storage_service.get_location(purpose='BL')[0]['uuid']
        to_add = [{'original_path': sourcepath,
                   'arrange_path': arrange_path}]

        # If it's a directory, fetch all the children
        if sourcepath.endswith('/'):
            to_add.extend(_get_arrange_directory_tree(backlog_uuid, sourcepath, arrange_path,))
        logging.debug('copy_to_arrange: files to be added: {}'.format(to_add))

        for entry in to_add:
            models.SIPArrange.objects.create(
                original_path=entry['original_path'],
                arrange_path=entry['arrange_path'],
                file_uuid=entry['file_uuid'],
            )

    if error is not None:
        response = {
            'message': error,
            'error': True,
        }
    else:
        response = {'message': 'Files added to the SIP.'}

    return helpers.json_response(response)


def _add_copied_files_to_arrange_log(sourcepath, full_destination):
    arrange_dir = _arrange_dir()

    # work out relative path within originals folder
    originals_subpath = sourcepath.replace(ORIGINAL_DIR, '')

    arrange_subpath = full_destination.replace(arrange_dir, '')
    dest_transfer_directory = arrange_subpath.split('/')[1]

    # add to arrange log
    transfer_logs_directory = os.path.join(arrange_dir, dest_transfer_directory, 'logs')
    if not os.path.exists(transfer_logs_directory):
        os.mkdir(transfer_logs_directory)
    arrange_log_filepath = os.path.join(transfer_logs_directory, 'arrange.log')
    transfer_root = os.path.join(arrange_dir, dest_transfer_directory)
    with open(arrange_log_filepath, "a") as logfile:
        if os.path.isdir(full_destination):
            # recursively add all files to arrange log 
            for dirname, dirnames, filenames in os.walk(full_destination):
                # print path to all filenames.
                for filename in filenames:
                    filepath = os.path.join(dirname, filename).replace(transfer_root, '')
                    relative_path_to_file_within_source_dir = '/'.join(filepath.split('/')[3:])
                    original_filepath = os.path.join(
                        originals_subpath[1:],
                        relative_path_to_file_within_source_dir
                    )
                    log_entry = original_filepath + ' -> ' + filepath.replace(transfer_root, '')[1:] + "\n"
                    logfile.write(log_entry)
        else:
            log_entry = originals_subpath[1:] + ' -> ' + full_destination.replace(transfer_root, '')[1:] + "\n"
            logfile.write(log_entry)

def download(request):
    shared_dir = os.path.realpath(helpers.get_client_config_value('sharedDirectoryMounted'))
    filepath = base64.b64decode(request.GET.get('filepath', ''))
    requested_filepath = os.path.realpath('/' + filepath)

    # respond with 404 if a non-Archivematica file is requested
    try:
        if requested_filepath.index(shared_dir) == 0:
            return helpers.send_file(request, requested_filepath)
        else:
            raise Http404
    except ValueError:
        raise Http404
