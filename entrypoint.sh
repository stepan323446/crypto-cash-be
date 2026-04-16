#!/bin/sh
uv run manage.py collectstatic --noinput
uv run manage.py migrate --noinput
exec "$@"