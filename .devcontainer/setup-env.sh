#!/usr/bin/env bash
# Generates the .env files for running the production compose stack inside a Codespace,
# pointing every public URL at the Codespace's forwarded port 80.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f apps/api/.env ]; then
  echo "apps/api/.env already exists, skipping env generation"
  exit 0
fi

PUBLIC_URL="https://${CODESPACE_NAME}-80.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
rand() { tr -dc 'A-Za-z0-9' </dev/urandom | head -c"$1"; }
SECRET_KEY=$(rand 50)
LIVE_SECRET=$(rand 32)
S3_KEY=$(rand 20)
S3_SECRET=$(rand 40)

cp .env.example .env
sed -i \
  -e "s|^AWS_ACCESS_KEY_ID=.*|AWS_ACCESS_KEY_ID=\"$S3_KEY\"|" \
  -e "s|^AWS_SECRET_ACCESS_KEY=.*|AWS_SECRET_ACCESS_KEY=\"$S3_SECRET\"|" \
  .env

cp apps/api/.env.example apps/api/.env
sed -i \
  -e "s|^AWS_ACCESS_KEY_ID=.*|AWS_ACCESS_KEY_ID=\"$S3_KEY\"|" \
  -e "s|^AWS_SECRET_ACCESS_KEY=.*|AWS_SECRET_ACCESS_KEY=\"$S3_SECRET\"|" \
  -e "s|^AWS_S3_ENDPOINT_URL=.*|AWS_S3_ENDPOINT_URL=\"http://plane-minio:9000\"|" \
  -e "s|^USE_MINIO=.*|USE_MINIO=1|" \
  -e "s|^MINIO_ENDPOINT_SSL=.*|MINIO_ENDPOINT_SSL=1|" \
  -e "s|^CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=\"$PUBLIC_URL\"|" \
  -e "s|^WEB_URL=.*|WEB_URL=\"$PUBLIC_URL\"|" \
  -e "s|^APP_BASE_URL=.*|APP_BASE_URL=\"$PUBLIC_URL\"|" \
  -e "s|^ADMIN_BASE_URL=.*|ADMIN_BASE_URL=\"$PUBLIC_URL\"|" \
  -e "s|^SPACE_BASE_URL=.*|SPACE_BASE_URL=\"$PUBLIC_URL\"|" \
  -e "s|^LIVE_BASE_URL=.*|LIVE_BASE_URL=\"$PUBLIC_URL\"|" \
  -e "s|^LIVE_SERVER_SECRET_KEY=.*|LIVE_SERVER_SECRET_KEY=\"$LIVE_SECRET\"|" \
  apps/api/.env
echo "SECRET_KEY=\"$SECRET_KEY\"" >>apps/api/.env

cat >apps/live/.env <<EOF
PORT=3000
API_BASE_URL="http://api:8000"
WEB_BASE_URL="$PUBLIC_URL"
LIVE_BASE_URL="$PUBLIC_URL"
LIVE_BASE_PATH="/live"
LIVE_SERVER_SECRET_KEY="$LIVE_SECRET"
REDIS_HOST=plane-redis
REDIS_PORT=6379
REDIS_URL="redis://plane-redis:6379/"
EOF

echo "Env files generated for $PUBLIC_URL"
