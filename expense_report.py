import os
import json
import logging
import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, Tuple

import gspread
from google.oauth2.service_account import Credentials
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def parse_amount(value: str) -> Decimal:
    """Parses a string amount (possibly with commas and spaces) into a Decimal. Returns 0 if empty or invalid."""
    if not value or not str(value).strip():
        return Decimal("0.00")
    
    clean_value = str(value).replace(",", "").strip()
    try:
        return Decimal(clean_value)
    except InvalidOperation:
        logger.warning(f"Could not parse '{value}' as a number. Defaulting to 0.")
        return Decimal("0.00")

def get_current_month_label() -> str:
    """Returns the current month label in the format expected in the sheet, e.g., 'May 2026'."""
    now = datetime.datetime.now()
    return now.strftime("%B %Y")

def fetch_sheet_data(credentials_file: str, spreadsheet_id: str, worksheet_name: str) -> Tuple[list, list]:
    """Fetches headers and rows from the specified Google Sheet worksheet."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly"
    ]
    
    if not os.path.exists(credentials_file):
        raise FileNotFoundError(f"Credentials file '{credentials_file}' not found.")
        
    credentials = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    client = gspread.authorize(credentials)
    
    try:
        sheet = client.open_by_key(spreadsheet_id)
    except Exception as e:
        raise ValueError(f"Failed to open spreadsheet with ID '{spreadsheet_id}': {e}")
        
    try:
        worksheet = sheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        raise ValueError(f"Worksheet '{worksheet_name}' not found in the spreadsheet.")
        
    data = worksheet.get_all_values()
    if not data:
        raise ValueError("Worksheet is completely empty.")
        
    headers = data[0]
    rows = data[1:]
    return headers, rows

def build_report(headers: list, rows: list, current_month_label: str) -> Tuple[Decimal, Decimal, Decimal, Dict[str, Decimal]]:
    """
    Processes the sheet data to calculate Income, Total Expense, Remaining Balance, 
    and a dict of category-wise expenses.
    """
    try:
        month_index = headers.index(current_month_label)
    except ValueError:
        raise ValueError(f"Current month column '{current_month_label}' not found in the sheet headers.")
        
    income = Decimal("0.00")
    total_expense = Decimal("0.00")
    # Using a dict to maintain insertion order (Python 3.7+ feature)
    category_expenses = {}
    
    income_found = False
    
    for row in rows:
        if not row:
            continue
            
        category_name = str(row[0]).strip()
        if not category_name:
            continue
            
        # Get value for current month, handle if row is shorter than month_index
        value_str = row[month_index] if len(row) > month_index else "0"
        amount = parse_amount(value_str)
        
        if category_name.lower() == "income":
            income += amount
            income_found = True
        else:
            total_expense += amount
            if amount > 0:
                category_expenses[category_name] = amount
                
    if not income_found:
        logger.warning("No 'Income' row found. Assuming income is 0.")
        
    remaining_balance = income - total_expense
    
    return income, total_expense, remaining_balance, category_expenses

def format_currency(amount: Decimal) -> str:
    """Formats amount in Indian Rupee style with comma separators and 2 decimals."""
    is_negative = amount < 0
    abs_amount = abs(amount)
    
    # Format absolute amount with standard commas first to get the decimal parts easily
    formatted = f"{abs_amount:,.2f}"
    parts = formatted.split(".")
    integer_part = parts[0].replace(",", "")
    decimal_part = parts[1]
    
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        rest = integer_part[:-3]
        rest_chunks = []
        while len(rest) > 0:
            rest_chunks.append(rest[-2:])
            rest = rest[:-2]
        rest_chunks.reverse()
        indian_integer_part = ",".join(rest_chunks) + "," + last_three
    else:
        indian_integer_part = integer_part
        
    sign = "-" if is_negative else ""
    return f"{sign}₹{indian_integer_part}.{decimal_part}"

def send_telegram_message(bot_token: str, chat_id: str, message: str) -> None:
    """Sends a plain text message to the specified Telegram chat."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    
    response = requests.post(url, json=payload)
    if not response.ok:
        raise RuntimeError(f"Failed to send Telegram message: HTTP {response.status_code} - {response.text}")
    logger.info("Telegram message sent successfully.")

def main():
    # Read environment variables
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    worksheet_name = os.environ.get("WORKSHEET_NAME", "category total")
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    credentials_file = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    
    missing_vars = []
    if not spreadsheet_id: missing_vars.append("SPREADSHEET_ID")
    if not bot_token: missing_vars.append("TELEGRAM_BOT_TOKEN")
    if not chat_id: missing_vars.append("TELEGRAM_CHAT_ID")
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
    current_month_label = get_current_month_label()
    logger.info(f"Targeting month: {current_month_label}")
    
    headers, rows = fetch_sheet_data(credentials_file, spreadsheet_id, worksheet_name)
    income, total_expense, remaining_balance, category_expenses = build_report(headers, rows, current_month_label)
    
    # Build Telegram message
    message_lines = [
        f"📊 Monthly Expense Update - {current_month_label}",
        "",
        f"💰 Income: {format_currency(income)}",
        f"💸 Total Expense So Far: {format_currency(total_expense)}",
        f"🟢 Remaining Balance: {format_currency(remaining_balance)}",
        "",
        "📂 Category-wise Expense So Far:"
    ]
    
    for cat, amount in category_expenses.items():
        message_lines.append(f"- {cat}: {format_currency(amount)}")
        
    message = "\n".join(message_lines)
    
    logger.info("Sending message to Telegram...")
    send_telegram_message(bot_token, chat_id, message)

if __name__ == "__main__":
    main()
