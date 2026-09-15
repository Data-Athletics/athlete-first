#!/bin/bash

NAME="$DB_name"
HOST="$DB_host"
PORT="$DB_port"
USER="$DB_user"
PASS="$DB_password"

echo "Waiting for database $NAME at $HOST:$PORT..."

until pg_isready --dbname="$NAME" --host="$HOST" --port="$PORT" --username="$USER"; do
  echo "$NAME is unavailable, trying again..."
  sleep 1
done

echo "Database $NAME is up and running!"