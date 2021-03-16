python manage.py collectstatic --noinput
web: gunicorn --chdir src --env DJANGO_SETTINGS_MODULE=src.settings src.wsgi --log-file - --log-level debug