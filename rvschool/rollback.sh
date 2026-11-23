#!/bin/sh
set -eu
cd /opt/rvschool-group1/deploy
backup=/opt/rvschool-group1/backups/petstore-status-20261123
if ! docker image inspect 'rvschool/petstore3:rollback-20261123' >/dev/null 2>&1; then
    gzip -dc "$backup/image.tar.gz" | docker image load
fi
python3 - <<'PY'
from pathlib import Path
import shutil
root = Path('/opt/rvschool-group1')
backup = root / 'backups/petstore-status-20261123/deploy'
path = root / 'deploy/compose.yml'
current = path.read_text()
original = (backup / 'compose.yml').read_text()
def bounds(text):
    start = text.index('  petstore-v3:\n')
    return start, text.index('  booker:\n', start)
a, b = bounds(current)
c, d = bounds(original)
service = original[c:d]
# The image archive always contains this explicitly saved rollback tag.
service = service.replace('image: swaggerapi/petstore3@sha256:97e5aa178dd4d160af9e31a900a685a943cd715cab7ba6ca6377fe976e95d1cf',
                          'image: rvschool/petstore3:rollback-20261123')
path.write_text(current[:a] + service + current[b:])
shutil.copyfile(backup / 'petstore-v3-openapi.yaml', root / 'deploy/petstore-v3-openapi.yaml')
PY
docker compose config --quiet
docker compose up -d --no-deps --no-build --force-recreate petstore-v3
