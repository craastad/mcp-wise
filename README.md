# Wise MCP Server

A MCP (Machine Communication Protocol) server that serves as a gateway for the Wise API, providing simplified access to Wise's recipient functionality.

## Features

- List all recipients from your Wise account via a simple MCP resource
- Check the balances of a profile
- Look up the status of a transfer
- Preview the rate and fee of a payment with a quote
- Send money step by step (quote, transfer, fund) with a review point before paying
- Read balance statements to reconcile incoming and outgoing payments
- Download the PDF receipt of a completed transfer
- Automatically handles authentication and profile selection
- Uses the Wise Sandbox API for development and testing
- Available as a Docker image for easy integration

## Requirements

- Python 3.12 or higher (only if installing directly)
- `uv` package manager (only if installing directly)
- Wise API token
- Docker (if using Docker image)

## Get an API token

https://wise.com/your-account/integrations-and-tools/api-tokens

Create a new token here.

## Installation

### Option 1: Direct Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/sergeiledvanov/mcp-wise
   cd wise-mcp
   ```

2. Set up the environment:
   ```bash
   cp .env.example .env
   # Edit .env to add your Wise API token
   ```

3. Install dependencies with `uv`:
   ```bash
   uv venv
   uv pip install -e .
   ```

### Option 2: Using Docker

You can build a Docker image:

```bash
docker build -t mcp-wise .
```

And add to Claude Code by adding it to your `.mcp.json`

```json
{
  "mcpServers": {
    "mcp-wise": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--init",
        "-e", "WISE_API_TOKEN=your_api_token_here",
        "-e", "WISE_IS_SANDBOX=true",
        "mcp-wise:latest"
      ]
    }
  }
}
```

Make sure to replace `your_api_token_here` with your actual Wise API token.

Make sure to also update your .mcp.json file to match your selected mode. We provide template files that you can use:

1. For stdio mode (default):
   ```bash
   cp .mcp.json.stdio .mcp.json
   ```

2. For HTTP mode:
   ```bash
   cp .mcp.json.http .mcp.json
   ```

These template files contain the appropriate configuration for each mode.

## Available MCP Resources

The server provides the following MCP resources:

### `list_recipients`

Returns a list of all recipients from your Wise account.

**Parameters**:
- `profile_type`: The type of profile to list recipients for. One of [personal, business]. Default: "personal"
- `currency`: Optional. Filter recipients by currency code (e.g., 'EUR', 'USD')

### `get_balances`

Returns the balances held by a profile, one entry per currency, with the
available and reserved amounts.

**Parameters**:
- `profile_type`: The type of profile to list balances for. One of [personal, business]. Default: "personal"
- `currency`: Optional. Only return the balance for this currency code (e.g., 'EUR')

### `get_recipient_requirements`

Fetches recipient requirements for creating a new recipient. If account details are provided, validates the account details against the requirements.

**Parameters**:
- `source_currency`: The source currency code (e.g., 'USD')
- `target_currency`: The target currency code (e.g., 'EUR')
- `source_amount`: The amount in the source currency
- `profile_type`: The type of profile to use. One of [personal, business]. Default: "personal"
- `account`: Optional. The recipient account details to validate against requirements. If not provided, returns the initial account requirements.

### `create_recipient`

Creates a new recipient with the provided account details.

**Parameters**:
- `profile_type`: The type of profile to use. One of [personal, business]. Default: "personal"
- `account`: The recipient account details compliant with Wise API requirements. This should include:
  - `accountHolderName`: Name of the account holder
  - `currency`: Target currency code (e.g., 'EUR')
  - `type`: Account type (e.g., 'iban', 'sort_code', etc.)
  - `details`: Object containing account-specific details (varies by currency and country)

### `send_money`

Sends money to a recipient using the Wise API.

**Parameters**:
- `profile_type`: The type of profile to use (personal or business)
- `source_currency`: Source currency code (e.g., 'USD') 
- `source_amount`: Amount in source currency to send
- `recipient_id`: The ID of the recipient to send money to
- `payment_reference`: Optional. Reference message for the transfer (defaults to "money")
- `source_of_funds`: Optional. Source of the funds (e.g., "salary", "savings")

### `create_quote`

Creates a quote and returns the rate, fee, target amount and expiry for
paying it from the balance. No money moves, so this previews a payment
before `send_money`, or starts the step-by-step
`create_quote` → `create_transfer` → `fund_transfer` flow.

**Parameters**:
- `source_currency`: Source currency code (e.g., 'EUR')
- `target_currency`: Target currency code; same as source for a same-currency transfer
- `source_amount`: Amount in source currency to send
- `recipient_id`: Optional. The ID of the recipient the quote is for (gives the exact fee)
- `profile_type`: The type of profile to use. One of [personal, business]. Default: "personal"

### `create_transfer`

Creates a transfer from a quote without paying it, so the amounts and
reference can be reviewed before `fund_transfer` moves the money. Use
`send_money` when no review step is needed.

**Parameters**:
- `recipient_id`: The ID of the recipient to send money to
- `quote_id`: The ID of a quote from `create_quote` for this recipient and amount
- `payment_reference`: Reference message shown to the recipient
- `source_of_funds`: Optional. Source of the funds (e.g., "salary", "savings")

### `fund_transfer`

Pays a transfer created with `create_transfer` from the profile's balance.
This moves money and may trigger an SCA challenge, in which case the
returned message contains the one-time token to approve.

**Parameters**:
- `transfer_id`: The ID of the transfer to fund
- `profile_type`: The type of profile that owns the transfer. One of [personal, business]. Default: "personal"

### `get_transfer`

Returns the current status and amounts of a transfer, for following a payment
after `send_money`.

**Parameters**:
- `transfer_id`: The ID of the transfer

### `list_balance_transactions`

Returns the transactions of a balance in a time window, newest first, for
reconciling incoming payments (`CREDIT`) and outgoing transfers (`DEBIT`).
Wise may require Strong Customer Authentication for statements on some
accounts.

**Parameters**:
- `currency`: Currency code of the balance to read (e.g., 'EUR')
- `profile_type`: The type of profile that holds the balance. One of [personal, business]. Default: "personal"
- `days`: Number of days to look back when `interval_start` is not given. Default: 30
- `interval_start`: Optional. Start of the window as an ISO 8601 timestamp
- `interval_end`: Optional. End of the window as an ISO 8601 timestamp. Default: now
- `transaction_type`: Optional. Only return `CREDIT` or `DEBIT` transactions
- `sender_name`: Optional. Only return transactions whose sender name contains this text

### `download_transfer_receipt`

Saves the PDF receipt of a completed transfer to a file on the machine
running the server, for use as proof of payment. The receipt is only
available once the transfer has reached status `outgoing_payment_sent`.
When the server runs in Docker, the path is inside the container.

**Parameters**:
- `transfer_id`: The ID of the transfer
- `output_path`: File path to write the PDF to; parent directories are created as needed

## Configuration

Configuration is done via environment variables, which can be set in the `.env` file:

- `WISE_API_TOKEN`: Your Wise API token (required)
- `WISE_IS_SANDBOX`: Set to true to use the Wise Sandbox API (default: false)
- `MODE`: MCP Server transport mode, either "http" or "stdio" (default: stdio)

## Development

### Project Structure

```
wise-mcp/
├── .env                # Environment variables (not in git)
├── .env.example        # Example environment variables
├── pyproject.toml      # Project dependencies and configuration
├── README.md           # This file
└── src/                # Source code
    ├── main.py         # Entry point
    └── wise_mcp/       # Main package
        ├── api/        # API clients
        │   └── wise_client.py # Wise API client
        ├── resources/  # MCP resources
        │   ├── balances.py    # Balances resource
        │   ├── recipients.py  # Recipients resource
        │   ├── statements.py  # Balance statements resource
        │   └── transfers.py   # Transfers resource
        └── app.py      # MCP application setup
```

### Adding New Features

To add new features:

1. Add new API client methods in `src/wise_mcp/api/wise_client.py`
2. Create new resources in `src/wise_mcp/resources/`
3. Import and register the new resources in `src/wise_mcp/app.py`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT