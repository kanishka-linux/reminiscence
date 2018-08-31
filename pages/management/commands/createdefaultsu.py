from django.core import management
from django.contrib.auth.models import User


class Command(management.BaseCommand):
    
    def handle(self, *args, **options):
        qlist = User.objects.filter(username='admin')
        if not qlist:
            print('creating default superuser: "admin" with password: "changepassword"')
            User.objects.create_superuser('admin', 'admin@reminiscence.org', 'changepassword')
        else:
            print('default admin already exists')
