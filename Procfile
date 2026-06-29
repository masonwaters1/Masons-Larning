web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py seed_courses && gunicorn config.wsgi --bind 0.0.0.0:$PORT
