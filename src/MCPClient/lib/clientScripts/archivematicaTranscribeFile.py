#!/usr/bin/python2

from __future__ import print_function
import os
import subprocess
import sys
from tempfile import gettempdir
from uuid import uuid4

path = '/usr/share/archivematica/dashboard'
if path not in sys.path:
    sys.path.append(path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.common'

from main.models import File, FileFormatVersion
from fpr.models import FPRule

path = '/usr/lib/archivematica/archivematicaCommon'
if path not in sys.path:
    sys.path.append(path)

from dicts import ReplacementDict
from executeOrRunSubProcess import executeOrRun


def main(file_path, file_uuid):
    file_ = File.objects.get(uuid=file_uuid)
    try:
        format = FileFormatVersion.objects.get(file_uuid=file_)
    except FileFormatVersion.DoesNotExist:
        print('File ID not found for "{}"; not transcribing'.format(file_.currentlocation))
        return 0
    rules = FPRule.objects.filter(format=format.format_version,
                                  purpose='transcription')

    if not rules:
        name = format.format_version.description
        print('No rules found for format {}; not transcribing'.format(name), file=sys.stderr)
        return 0

    rd = ReplacementDict.frommodel(file_=file_, type_='file')

    print(str(rd))

    for rule in rules:
        script = rule.command.command
        if rule.command.script_type in ('bashScript', 'command'):
            script, = rd.replace(script)
            args = []
        else:
            args = rd.to_gnu_options

        exitstatus, stdout, stderr = executeOrRun(rule.command.script_type,
                                                  script, arguments=args)


if __name__ == '__main__':
    file_path = sys.argv[1]
    file_uuid = sys.argv[2]
    transcribe = sys.argv[3]

    if transcribe == 'False':
        print('Skipping transcription')
        sys.exit(0)

    sys.exit(main(file_path, file_uuid))
