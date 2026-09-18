#!/bin/bash
# Reference: https://github.com/mrts/docker-postgresql-multiple-databases/blob/master/create-multiple-postgresql-databases.sh

set -eu

function create_database() {
	local database="$1"
	local user="$POSTGRES_USER"
  
	echo "  Creating database '$database' and assigning to user '$user'"
	psql -v ON_ERROR_STOP=1 --username "$user" <<-EOSQL
	    CREATE DATABASE $database;
	    GRANT ALL PRIVILEGES ON DATABASE $database TO $user;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"

	for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
		create_database "$db"
	done
  
	echo "Multiple databases created"
fi