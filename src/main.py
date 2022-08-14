from __future__ import print_function

import os.path
import requests
import schedule
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SAMPLE_SPREADSHEET_ID = '1_NZ38z8G0lMKHHhLbn3uM9ZXUqrLkNi_mUVD6xf2Gmw'
SAMPLE_RANGE_NAME = 'page1!B2:B3'

def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def create_sheets_service(creds):
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    return sheet

def get_last_ip(sheet_service, sheet_id, range):
    result = sheet_service.values().get(spreadsheetId=sheet_id,
                                    range=range).execute()
    values = result.get('values', [])
    if not values:
        print('No data found.')
        return
    ip = values[0][0]
    return ip

def set_ip(sheet_service, sheet_id, range, ip):
    sheet_service.values().update(spreadsheetId=sheet_id, range=range,
    valueInputOption="USER_ENTERED", body={"values": [[ip]]}).execute()

def get_public_ip():
    public_ip = requests.get('https://api.ipify.org').text
    return public_ip

def run():
    print("running update_ip_job")
    credentials = authenticate()
    try:
        sheet_service = create_sheets_service(credentials)
        last_ip = get_last_ip(sheet_service=sheet_service, sheet_id=SAMPLE_SPREADSHEET_ID, range="page1!B3")
        print("ultimo ip:" + last_ip)
        current_ip = get_public_ip()
        print("ip atual:" + current_ip)
        if (last_ip != current_ip):
            set_ip(sheet_service=sheet_service, sheet_id=SAMPLE_SPREADSHEET_ID, range="page1!B3", ip=current_ip)
            print("ip atualizado no google sheets")
    except HttpError as err:
        print(err)

def main():
    print("executing job for the first time")
    run()
    print("scheduling job execution for every 30 minutes")
    schedule.every(30).minutes.do(run)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    main()
