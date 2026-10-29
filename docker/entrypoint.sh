#!/bin/sh
set -e

echo "Memorie [entrypoint]: applying migrations…"
python manage.py migrate --noinput

echo "Memorie [entrypoint]: collecting static files…"
python manage.py collectstatic --noinput

# Create the server owner, once, from environment variables.
if [ -n "$ADMIN_USERNAME" ] && [ -n "$ADMIN_PASSWORD" ]; then
python manage.py shell -c "
from django.contrib.auth.models import User
from memories.models import UserProfile
import os

if not User.objects.filter(username=os.environ['ADMIN_USERNAME']).exists():
    user = User.objects.create_superuser(
        username=os.environ['ADMIN_USERNAME'],
        email=os.environ.get('ADMIN_EMAIL', ''),
        password=os.environ['ADMIN_PASSWORD'],
        first_name=os.environ.get('ADMIN_NAME', ''),
    )
    UserProfile.objects.create(user=user, full_name=os.environ.get('ADMIN_NAME', os.environ['ADMIN_USERNAME']))
    print('Memorie [entrypoint]: created owner account', user.username)
else:
    print('Memorie [entrypoint]: owner account already exists — skipping')
"
fi

echo "Memorie [entrypoint]: starting gunicorn…"
exec gunicorn oseiantwi.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --timeout 120
