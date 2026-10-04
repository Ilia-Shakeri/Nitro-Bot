# DMB server automation

## Chosen path

The worker runs continuously inside Docker on the Linux VPS. It reads one leased
release at a time from the internal API, downloads its WAV and cover from MinIO,
opens Firefox in headless mode, submits DMB, records evidence, and reports the
result. No desktop, VNC session, laptop, or visible browser is required.

## Options

| Path | Score | Use |
| --- | ---: | --- |
| Official DMB direct interface | 10/10 | Best long-term path. Ask the Label Manager for the interface contract and credentials. |
| Official XML or CSV import | 9/10 | Good for batches if DMB enables it and supplies the exact schema. |
| Headless Firefox worker | 8.5/10 | Implemented now. Works with the current DMB browser workflow on the VPS. |
| Visible laptop run | 4/10 | Emergency fallback only. Sleep and network loss stop it. |
| Replayed private HTTP requests | 2/10 | Do not use. Private endpoints, cookies, and CSRF can change without notice. |

Kontor New Media publicly states that DMB supports XML, CSV, and a direct
database interface on request. No public interface contract is available in
this repository. A direct driver must not be built by guessing private calls.

## Required environment

```dotenv
DMB_BROWSER_MODE=headless
DMB_HEALTH_PORT=8081
DMB_CREATE_ENABLED=false
DMB_EDIT_ENABLED=false
DMB_EDIT_SUBMIT_ENABLED=false
DMB_RECOVERY_ENABLED=false
DMB_TARGET_RELEASE_ID=
DMB_SUCCESS_TOPIC_ID=44
DMB_ERROR_TOPIC_ID=43
DMB_REVIEW_TOPIC_ID=42
DMB_USERNAME=replace_me
DMB_PASSWORD=replace_me
SELENIUM_SECRET_KEY=replace_with_long_random_value
DMB_REVIEW_SECRET_KEY=replace_with_different_long_random_value
```

Keep all delivery flags false for the first deployment. Turn on create only
after an approved staging submission. Turn on edit only after its own approved
staging submission.

For one approved live test, set `DMB_TARGET_RELEASE_ID` to that release ID.
The backend then leases only that exact row. Leave it empty for normal FIFO
queue work. A create is complete only after the worker saves the album, reopens
the returned DMB ID, matches its EAN, clicks Publish, and records final proof.

## Safe VPS rollout

```bash
git pull --ff-only
docker compose build backend dmb-automation
docker compose up -d db minio redis backend
docker compose exec backend alembic upgrade head
docker compose up -d dmb-automation
docker compose ps dmb-automation
docker compose logs --tail=100 dmb-automation
```

The health endpoint stays inside the Docker network. Verify it without opening
a public port:

```bash
docker compose exec dmb-automation python -c "import os,urllib.request; print(urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"DMB_HEALTH_PORT\"]}/health/live').read().decode())"
```

`/health/live` proves the worker process and health server are alive.
`/health/ready` also requires a successful queue poll and a closed circuit.

## Failure rules

- One worker handles one claimed release at a time.
- The backend lease and browser heartbeat protect an active job.
- A failure before the submit checkpoint becomes retryable.
- A failure after the checkpoint becomes manual verification required.
- Retry waits for an allowed admin click in the DMB error topic.
- Save records the exact DMB ID. Recovery resumes that album only after an
  allowed admin click in the DMB review topic.
- An uncertain result opens the circuit and stops new claims.
- An open circuit may run exact recovery work, but never a fresh create.
- The `dmb-results` directory must remain persistent for screenshots and logs.
- Success, error, and review reports use topics 44, 43, and 42. Error and review
  reports attach the saved browser screenshot when one exists.

## Moving to the official interface

Ask the Label Manager for:

1. Interface type: direct API, XML, CSV, SFTP, or another transport.
2. Exact schema and validation rules.
3. Sandbox credentials and endpoint.
4. Idempotency or duplicate prevention contract.
5. Status, error, EAN, and ISRC response contract.
6. Update, publish, takedown, and asset-upload rules.

After those exist, add a second delivery driver behind the same lease,
checkpoint, evidence, circuit, and manual-review contract. Keep the headless
driver as rollback until staging proves parity.
