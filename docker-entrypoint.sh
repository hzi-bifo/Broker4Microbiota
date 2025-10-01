#!/usr/bin/env bash
set -Eeuo pipefail

: "${PROJECT_DIR:=project}"
: "${ROLE:=web}"               # web | worker
: "${RUN_MIGRATIONS:=1}"       # only when ROLE=web
: "${RUN_COLLECTSTATIC:=1}"    # only when ROLE=web

if [[ ! -f "$PROJECT_DIR/manage.py" ]]; then
  echo "❌ manage.py not found at '$PROJECT_DIR/manage.py'. Set PROJECT_DIR correctly."
  exit 1
fi

echo "🔧 Using Python: $(python --version)"
echo "📂 Project dir: $PROJECT_DIR"
echo "🧩 Role: $ROLE"

# Serialize ops in case multiple services ever try to run them
lock_migrate="/tmp/django.migrate.lock"
lock_static="/tmp/django.static.lock"

run_migrate() {
  echo "🗄️ migrate..."
  flock -w 120 "$lock_migrate" bash -lc 'python "'"$PROJECT_DIR"'/manage.py" migrate --noinput'
}

run_collectstatic() {
  echo "📁 collectstatic..."
  flock -w 120 "$lock_static" bash -lc 'python "'"$PROJECT_DIR"'/manage.py" collectstatic --noinput'
}

if [[ "$ROLE" == "web" ]]; then
  [[ "$RUN_MIGRATIONS" == "1" ]] && run_migrate || echo "↷ skipping migrate"
  [[ "$RUN_COLLECTSTATIC" == "1" ]] && run_collectstatic || echo "↷ skipping collectstatic"
else
  echo "↷ worker role: skipping migrate/collectstatic"
fi

# Optional superuser on web only
if [[ "$ROLE" == "web" && "${DJANGO_CREATE_SUPERUSER:-0}" == "1" ]]; then
  [[ -n "${DJANGO_SU_PASSWORD:-}" ]] || { echo "❌ set DJANGO_SU_PASSWORD"; exit 1; }
  echo "👤 Ensuring superuser exists..."
  python "$PROJECT_DIR/manage.py" shell -c "
from django.contrib.auth import get_user_model
User=get_user_model()
u='${DJANGO_SU_USERNAME:-admin}'; e='${DJANGO_SU_EMAIL:-admin@example.com}'; p='${DJANGO_SU_PASSWORD}'
User.objects.filter(username=u).exists() or User.objects.create_superuser(u,e,p)
print('✅ Ready.')
"
fi

echo "🚀 Starting: $*"
exec "$@"

