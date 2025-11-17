from __future__ import annotations

import json
import os
from typing import Dict, List

import gspread
from google.oauth2.service_account import Credentials

_SPREADSHEET = None


def _get_spreadsheet():
    global _SPREADSHEET
    if _SPREADSHEET is not None:
        return _SPREADSHEET

    creds_raw = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if not creds_raw:
        raise RuntimeError("Missing GOOGLE_SHEETS_CREDENTIALS")
    creds_info = json.loads(creds_raw)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(credentials)
    sheet_id = os.environ["GOOGLE_SHEETS_SPREADSHEET_ID"]
    _SPREADSHEET = client.open_by_key(sheet_id)
    return _SPREADSHEET


def read_sheet(worksheet: str) -> List[List[str]]:
    spreadsheet = _get_spreadsheet()
    result = spreadsheet.values_get(worksheet)
    return result.get("values", [])


def write_sheet(worksheet: str, columns: List[str], rows: List[List[str]]) -> None:
    spreadsheet = _get_spreadsheet()
    data = [columns] + rows
    spreadsheet.values_update(
        worksheet,
        params={"valueInputOption": "RAW"},
        body={"values": data},
    )
