import os
import reminiscence
from django.conf import settings
from django.core import management
import shutil

BASE_DIR = os.path.dirname(reminiscence.__file__)

class Command(management.BaseCommand):
    
    help = 'Apply docker or default settings'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--docker', dest='docker', default=None,
            help='Apply docker specific settings',
        )
        parser.add_argument(
            '--default', dest='default', default=None,
            help='Apply default settings',
        )
    
    def handle(self, *args, **options):
        original = os.path.join(BASE_DIR, 'settings.py')
        dock = os.path.join(BASE_DIR, 'dockersettings.py')
        default = os.path.join(BASE_DIR, 'defaultsettings.py')
        optdock = options.get('docker')
        optdef = options.get('default')
        if optdock and optdock.lower() == 'yes':
            shutil.copy(dock, original)
            print('docker settings copied')
        elif optdef and optdef.lower() == 'yes':
            shutil.copy(default, original)
            print('default settings copied')
