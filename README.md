# Category Total Expense Reporter

A production-ready Python automation project that reads data from a Google Sheet and sends a daily Telegram summary message at 11:00 PM IST via GitHub Actions.

## Features
- Fetches real-time financial data from a private Google Sheet.
- Automatically targets the current month based on system time (e.g., "May 2026").
- Calculates total income, total expense, and remaining balance.
- Filters out zero-value or blank categories.
- Safely handles currency formatting including commas and blank cells.
- Sends a well-formatted summary message via Telegram Bot.

## Expected Telegram Output

```text
📊 Monthly Expense Update - May 2026

💰 Income: ₹1,13,074.00
💸 Total Expense So Far: ₹82,776.00
🟢 Remaining Balance: ₹30,298.00

📂 Category-wise Expense So Far:
- Rent: ₹18,300.00
- Investment: ₹23,000.00
- Emergency Fund: ₹20,000.00
- Grocery: ₹440.00
- Entertainment: ₹1,650.00
- Grooming: ₹1,444.00
- Medicine: ₹3,878.00
- Others: ₹140.00
- Travel: ₹1,840.00
- EB & EC: ₹1,477.00
- Relatives: ₹3,716.00
- EMI: ₹7,191.00
```

## Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a `credentials.json` file in the root directory by downloading your Service Account JSON key from Google Cloud Console.
3. Set your environment variables:
   ```bash
   export SPREADSHEET_ID="your_google_sheet_id_here"
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   # Optional overrides:
   # export WORKSHEET_NAME="category total"
   # export GOOGLE_CREDENTIALS_FILE="credentials.json"
   ```
4. Run the script:
   ```bash
   python expense_report.py
   ```

## Setup Google Service Account
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **Google Sheets API**.
3. Create a Service Account and generate a JSON key.
4. **Important**: Open your Google Sheet, click "Share", and add the `client_email` from your Service Account JSON as a Viewer or Editor.

## GitHub Actions Setup
The workflow is scheduled to run daily at 11:00 PM IST (17:30 UTC).

You need to add the following secrets to your GitHub repository:
- `GOOGLE_CREDENTIALS_JSON`: The complete raw JSON string of your Service Account key.
- `SPREADSHEET_ID`: The ID of your Google Sheet (found in the URL `d/<SPREADSHEET_ID>/edit`).
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot API token (from BotFather).
- `TELEGRAM_CHAT_ID`: The Telegram chat ID where you want the messages sent.

To set up secrets:
1. Go to your GitHub repository.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret** for each variable listed above.

## Schedule Information
The workflow cron is defined as `30 17 * * *` which runs at 17:30 UTC every day.
UTC is 5 hours and 30 minutes behind IST, meaning 17:30 UTC successfully corresponds to 11:00 PM IST.
