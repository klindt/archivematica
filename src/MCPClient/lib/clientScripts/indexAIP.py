#!/usr/bin/python2 -OO

import ConfigParser
import os
import sys

path = "/usr/lib/archivematica/archivematicaCommon"
if path not in sys.path:
    sys.path.append(path)
path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

import elasticSearchFunctions
from executeOrRunSubProcess import executeOrRun
import storageService as storage_service

def index_aip():
    """ Write AIP information to ElasticSearch. """
    sip_uuid = sys.argv[1]  # %sip_uuid%
    sip_name = sys.argv[2]  # %sip_name%
    aip_path = sys.argv[3]  # %SIPDirectory%%sip_name%-%sip_uuid%.7z

    # Check if ElasticSearch is enabled
    client_config_path = '/etc/archivematica/MCPClient/clientConfig.conf'
    config = ConfigParser.SafeConfigParser()
    config.read(client_config_path)
    elastic_search_disabled = False
    try:
        elastic_search_disabled = config.getboolean(
            'MCPClient', "disableElasticsearchIndexing")
    except ConfigParser.NoOptionError:
        pass
    if elastic_search_disabled:
        print 'Skipping indexing: indexing is currently disabled in {}.'.format(client_config_path)
        return (0)

    print 'sip_uuid', sip_uuid
    aip_info = storage_service.get_file_info(uuid=sip_uuid)
    print 'aip_info', aip_info
    aip_info = aip_info[0]

    # Extract METS file, so Elastic Search can parse it
    zip_mets_path = os.path.join(
        "{}-{}".format(sip_name, sip_uuid),
        "data",
        'METS.{}.xml'.format(sip_uuid))
    mets_path = os.path.join('/tmp', "METS.{}.xml".format(sip_uuid))
    command = 'atool --cat {aip_path} {zip_mets_path} > {mets_path}'.format(
        aip_path=aip_path, zip_mets_path=zip_mets_path, mets_path=mets_path)
    print 'Extracting METS file with:', command
    exit_code, _, _ = executeOrRun("bashScript", command, printing=True)
    if exit_code != 0:
        print >>sys.stderr, "Error extracting"
        sys.exit(1)

    elasticSearchFunctions.connect_and_index_aip(
        sip_uuid,
        sip_name,
        aip_info['current_full_path'],
        mets_path,
        size=aip_info['size'])
    elasticSearchFunctions.connect_and_remove_sip_transfer_files(sip_uuid)

    os.remove(mets_path)

if __name__ == '__main__':
    index_aip()
