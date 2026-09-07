# Changelog

All notable changes to this project are listed here, newest first. The
format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Each version corresponds to a git tag `vX.Y.Z` and to the `version` in
`pyproject.toml`.

## [0.2.0] - 2026-09-07

### Added

- `list_profiles` tool returning every profile the token can see, with the default marked.
- `WISE_PROFILE_ID` environment variable as the default profile, and a `profile_id` argument on every profile-bound tool.
- `download_balance_statement` tool: pdf, csv, xlsx or json, for a `month` or an explicit date window of at most 469 days.
- Strong Customer Authentication: one-time tokens are signed with the key at `WISE_PRIVATE_KEY_PATH` (optionally `WISE_PRIVATE_KEY_PASSPHRASE`).

### Changed

- Wise calls use the calendar-versioned API paths under `WISE_API_VERSION` (`2026Q3`) on `api.wise.com` / `api.wise-sandbox.com`. Only the pdf, csv and xlsx balance-statement downloads remain on the legacy `/v1` path, since the versioned API serves `statement.json` alone.
- `WISE_IS_SANDBOX` defaults to false.
- Profiles are listed through the endpoint that returns every business profile on the login, not only the first.

### Fixed

- Profile names are read from the nested `details` block that older profile responses use.
- `fund_transfer` no longer prints to stdout.
- Removed the broken `src/main.py`.

## [0.1.0] - 2026-09-07

### Added

- Recipient tools: `list_recipients`, `get_recipient_requirements`, `create_recipient` and `send_money`.
- `get_balances` tool listing the standard balances of a profile.
- `create_quote`, `create_transfer` and `fund_transfer` tools for the step-by-step payment flow, and `get_transfer` for following a payment.
- `list_balance_transactions` tool reading a balance statement for reconciliation.
- `download_transfer_receipt` tool saving the PDF receipt of a completed transfer.
- Request helpers on `WiseApiClient` and a pytest suite that mocks the HTTP layer.
