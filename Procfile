web: cd erp_chvs && gunicorn erp_chvs.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
release: cd erp_chvs && python manage.py migrate --noinput && python manage.py collectstatic --noinput
