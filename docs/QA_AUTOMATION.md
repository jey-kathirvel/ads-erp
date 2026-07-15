# ADS ERP P0 QA automation

The browser suite uses Playwright with pytest and must target a dedicated QA environment. It is deliberately excluded from the normal unit-test command.

## Local setup

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
```

Set `QA_BASE_URL`, `QA_ADMIN_EMAIL`, and `QA_ADMIN_PASSWORD`, then run:

```bash
pytest tests/e2e -m p0 --browser chromium --headed
```

Use `pytest` without arguments for the fast backend suite. Browser tests only run when selected with `-m p0` or `-m e2e`.

## Safety

- Never point mutation tests at production.
- Use a disposable QA administrator and sanitized database snapshot.
- Tests that create or delete records must carry the `mutation` marker and require `QA_ALLOW_MUTATIONS=true`.
- GitHub credentials belong in the protected `qa` environment secrets.

## Current P0 coverage

- Health endpoint
- Login rendering and password visibility control
- Invalid credential rejection
- Authentication enforcement for critical routes
- Administrator login/logout
- Critical billing, booking, inventory, backup, reporting, and user-page smoke checks

The next increment should add isolated data factories and transactional workflows for invoice creation, booking lifecycle, stock movement, backup lifecycle, and inactive-user deletion.
