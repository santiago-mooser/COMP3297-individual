web: gunicorn --chdir src --env DJANGO_SETTINGS_MODULE=src.settings src.wsgi --log-file - --log-level debug
python manage.py collectstatic --noinput
manage.py migrate