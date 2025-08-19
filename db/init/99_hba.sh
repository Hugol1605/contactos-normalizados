#!/usr/bin/env bash
set -e
if [ -f /docker-entrypoint-initdb.d/pg_hba_custom.conf ]; then
  cat /docker-entrypoint-initdb.d/pg_hba_custom.conf >> "$PGDATA/pg_hba.conf"
fi
