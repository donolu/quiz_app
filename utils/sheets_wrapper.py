from __future__ import annotations

import json
import os
from typing import Dict, List

import gspread
from google.oauth2.service_account import Credentials


class SheetsClient:
    def __init__(self):
        creds_raw = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_raw:
            raise RuntimeError('Missing GOOGLE_SHEETS_CREDENTIALS')
        creds_info = json.loads(creds_raw)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
        self.client = gspread.authorize(credentials)
        sheet_id = os.environ['GOOGLE_SHEETS_SPREADSHEET_ID']
        self.spreadsheet = self.client.open_by_key(sheet_id)

    def fetch(self, worksheet: str, columns: List[str]) -> List[Dict[str, str]]:
        ws = self.spreadsheet.worksheet(worksheet)
        try:
            records = ws.get_all_records()
            return records
        except Exception as exc:
            if 'Quota exceeded' in str(exc):
                return self._fetch_via_query(ws, columns)
            raise

    def _fetch_via_query(self, ws, columns: List[str]) -> List[Dict[str, str]]:
        range_label = ws.title
        values = ws.spreadsheet.values_get(range_label).get('values', [])
        if not values:
            return []
        header = values[0]
        output = []
        for row in values[1:]:
            record = {col: row[idx] if idx < len(row) else '' for idx, col in enumerate(header)}
            output.append(record)
        return output

    def update(self, worksheet: str, columns: List[str], rows: List[List[str]]):
        ws = self.spreadsheet.worksheet(worksheet)
        data = [columns] + rows
        ws.clear()
        ws.update(data)
