RV School Petstore v3 deployment

The POST /pet controller validates a non-null status before PetData.addPet.
Allowed values are available, pending and sold. Other strings return
HTTP 404 and {"code":404,"message":"Invalid pet status"} without saving.
Missing or null status keeps the previous behavior. Other controller methods
and dependencies are unchanged. The deployed OpenAPI documents this contract.

The Dockerfile compiles only PetController against the libraries from the
digest-pinned original Petstore 1.0.29 WAR. The original source is retained
for bytecode comparison; the runtime image contains the patched WAR and spec.

Build from the repository root:
  docker build -f rvschool/Dockerfile -t rvschool/petstore3:status-validation-20261123 .

The tracked compose.yml mirrors the lab stack with paths relative to rvschool/.
Build and recreate only Petstore v3:
  docker compose -f rvschool/compose.yml build petstore-v3
  docker compose -f rvschool/compose.yml up -d --no-deps petstore-v3

The active host Compose file at /opt/rvschool-group1/deploy/compose.yml points
to this checkout and rvschool/Dockerfile. Its mounted OpenAPI file has the same
contents as src/main/resources/openapi.yaml; copy updates there before restart.
The tracked Compose snapshot mounts the source spec directly.

Validation on the public lab after container recreation: 38/38 checks passed.
The script uses randomly allocated IDs, verifies they are initially absent,
and removes its records in a finally block. Run:
  python3 rvschool/verify.py --out /tmp/petstore-validation.json
Checks cover valid statuses, unknown and an arbitrary invalid string, rejected
overwrite preserving all fields, absent/null status, PUT, GET, DELETE and the
served OpenAPI. validation-summary.json contains checks and cleanup results.
The source release reproduces the deployed controller bytecode. Only the
addPet(RequestContext, Pet) method changed; all other WAR entries are identical.

Rollback on the existing host:
  sh /opt/rvschool-group1/petstore-v3/rollback.sh
Backups: /opt/rvschool-group1/backups/petstore-status-20261123/
The rollback restores only the Petstore v3 Compose service and prior OpenAPI,
loads the archived original image when needed and recreates only petstore-v3.

Petstore uses JVM memory for data. Recreating its container resets the data
to the initial set. File/image backups do not contain a JVM memory snapshot.
