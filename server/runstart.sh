#!/bin/bash
cd /app/server/
exec gunicorn --config /app/server/config.py wsgi:app