from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from getpass import getpass


class Command(BaseCommand):
    help = 'Create a new sequencing facility staff member account'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the staff member (e.g., john.doe)'
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email address for the staff member'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            help='First name of the staff member'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            help='Last name of the staff member'
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Grant superuser privileges (full Django admin access)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating Sequencing Facility Staff Account\n'))
        
        # Get username
        username = options.get('username')
        if not username:
            username = input('Username (e.g., john.doe): ').strip()
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User {username} already exists!'))
            return
        
        # Get email
        email = options.get('email')
        if not email:
            email = input('Email address: ').strip()
        
        # Get first name
        first_name = options.get('first_name')
        if not first_name:
            first_name = input('First name: ').strip()
        
        # Get last name
        last_name = options.get('last_name')
        if not last_name:
            last_name = input('Last name: ').strip()
        
        # Get password
        password = getpass('Password: ')
        password_confirm = getpass('Confirm password: ')
        
        if password != password_confirm:
            self.stdout.write(self.style.ERROR('Passwords do not match!'))
            return
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Always grant staff status for admin dashboard access
            user.is_staff = True
            
            # Optionally grant superuser status
            if options.get('superuser'):
                user.is_superuser = True
                self.stdout.write(self.style.WARNING('Granting superuser privileges...'))
            
            user.save()
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created staff account for {first_name} {last_name}!'))
            self.stdout.write(f'  Username: {username}')
            self.stdout.write(f'  Email: {email}')
            self.stdout.write(f'  Staff status: ✓')
            self.stdout.write(f'  Superuser status: {"✓" if user.is_superuser else "✗"}')
            self.stdout.write(f'\n{first_name} can now log in at /admin-dashboard/')
            
            if not user.is_superuser:
                self.stdout.write(self.style.NOTICE(
                    '\nNote: This user has access to the admin dashboard but not the Django admin.\n'
                    'To grant full Django admin access, use --superuser flag.'
                ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating user: {str(e)}'))