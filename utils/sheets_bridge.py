from __future__ import annotations

import json
import os
from typing import List

import gspread
from google.oauth2.service_account import Credentials


def _build_client():
    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_raw:
        raise RuntimeError("Missing GOOGLE_SHEETS_CREDENTIALS")
    creds_info = json.loads(creds_raw)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(credentials)
    spreadsheet_id = os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"]
    spreadsheet = client.open_by_key(spreadsheet_id)
    return spreadsheet


def read_sheet(worksheet: str) -> List[List[str]]:
    spreadsheet = _build_client()
    response = spreadsheet.values_get(worksheet)
    return response.get("values", [])


def write_sheet(worksheet: str, columns: List[str], rows: List[List[str]]) -> None:
    spreadsheet = _build_client()
    data = [columns] + rows
    spreadsheet.values_update(
        worksheet,
        params={"valueInputOption": "RAW"},
        body={"values": data},
    )
