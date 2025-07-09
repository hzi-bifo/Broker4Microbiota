# Sequencing Facility Staff Setup Guide

This guide explains how to set up multiple staff accounts for sequencing facility personnel who need access to the admin dashboard.

## Overview

The system already supports multiple admin users. Each staff member at the sequencing facility can have their own account with:
- Their own username that appears in activity logs
- Access to the admin dashboard (`/admin-dashboard/`)
- Access to Django admin interface (`/admin/`)
- Ability to update order statuses, add notes, and manage the workflow

## Setting Up Staff Accounts

### Method 1: Using Django Shell (Recommended for initial setup)

1. Activate your virtual environment:
```bash
source venv/bin/activate
cd project
```

2. Open Django shell:
```bash
python manage.py shell
```

3. Create a new staff user:
```python
from django.contrib.auth.models import User

# Create a new staff member
user = User.objects.create_user(
    username='jane.smith',  # Use a clear username format
    email='jane.smith@sequencing-facility.com',
    password='secure_password_here',
    first_name='Jane',
    last_name='Smith'
)

# Grant staff permissions
user.is_staff = True  # Allows access to admin dashboard
user.save()

# Optional: Make them a superuser if they need full Django admin access
# user.is_superuser = True
# user.save()
```

4. Exit the shell:
```python
exit()
```

### Method 2: Using Django Admin Interface

1. Log in as a superuser at `/admin/`

2. Navigate to **Users** under **Authentication and Authorization**

3. Click **Add User** and fill in:
   - Username: Use a clear format like `firstname.lastname` or `facility_john`
   - Password: Set a secure password

4. On the next screen, set:
   - First name: Their actual first name
   - Last name: Their actual last name
   - Email address: Their facility email
   - **Staff status**: ✓ Check this box (REQUIRED for admin dashboard access)
   - **Superuser status**: Only check if they need full Django admin access

5. Save the user

### Method 3: Create a Management Command (For Multiple Users)

Create a file `project/app/management/commands/create_facility_staff.py`:

```python
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create sequencing facility staff accounts'

    def handle(self, *args, **options):
        # Define your staff members
        staff_members = [
            {
                'username': 'john.doe',
                'email': 'john.doe@facility.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'password': 'ChangeMe123!'  # Have users change on first login
            },
            {
                'username': 'mary.johnson',
                'email': 'mary.johnson@facility.com',
                'first_name': 'Mary',
                'last_name': 'Johnson',
                'password': 'ChangeMe123!'
            },
            # Add more staff members as needed
        ]

        for staff_data in staff_members:
            username = staff_data['username']
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'User {username} already exists, skipping...')
                continue
            
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=staff_data['email'],
                password=staff_data['password'],
                first_name=staff_data['first_name'],
                last_name=staff_data['last_name']
            )
            
            # Make them staff
            user.is_staff = True
            user.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully created staff user: {username}'
            ))
        
        self.stdout.write(self.style.SUCCESS(
            '\nRemember to have users change their passwords on first login!'
        ))
```

Then run:
```bash
python manage.py create_facility_staff
```

## Username Best Practices

To ensure clear identification in activity logs:

1. **Use consistent format**: 
   - `firstname.lastname` (e.g., `john.doe`)
   - `facility_firstname` (e.g., `facility_john`)
   - `firstname_lastinitial` (e.g., `john_d`)

2. **Make it readable**: The username appears in activity logs, so avoid cryptic usernames

3. **Include full names**: Always fill in first_name and last_name fields

## What Staff Members Can Do

With `is_staff = True`, users can:
- Access `/admin-dashboard/` (the custom admin interface)
- View all orders and projects
- Update order statuses
- Add notes (internal and user-visible)
- Reject orders with feedback
- Export order data
- View complete activity history

## What They Cannot Do (unless `is_superuser = True`)

- Cannot modify Django models directly
- Cannot create/delete other users
- Cannot access Django admin panels they don't have specific permissions for

## Activity Tracking

All actions by staff members are automatically tracked:
- Their username appears in the activity log
- The timestamp of their action is recorded
- The type of action (status change, note, rejection) is logged
- Any notes or reasons they provide are stored

Example display in activity log:
```
Nov 25, 2024 14:30 • jane.smith
Order #123 - Microbiome Study 2024
[Status Change] Ready for Sequencing → Sequencing in Progress
```

## Security Recommendations

1. **Strong Passwords**: Enforce strong passwords for all staff accounts
2. **Regular Updates**: Have staff change passwords periodically
3. **Remove Access**: When staff leave, immediately set `is_active = False`
4. **Audit Trail**: The activity log provides a complete audit trail of who did what

## Testing a New Staff Account

After creating a new staff account:

1. Log out of any current session
2. Log in with the new credentials at `/`
3. You should see the "Admin Dashboard" link in the navigation
4. Click to access `/admin-dashboard/`
5. Make a test action (add a note) and verify the username appears correctly

## Troubleshooting

**"Permission denied" when accessing admin dashboard:**
- Ensure `is_staff = True` is set for the user
- Check that the user is logged in

**Username not appearing in logs:**
- Verify the user is authenticated when making changes
- Check that first_name and last_name are set for better display

**Cannot see Django admin interface:**
- This requires `is_superuser = True` or specific model permissions
- Most facility staff only need access to the custom admin dashboard