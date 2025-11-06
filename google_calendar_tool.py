# google_calendar_tool.py
from langchain.tools import BaseTool
from googleapiclient.discovery import build
from google.oauth2 import service_account
import datetime
import json

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = "/path/a/credentials.json"  # pon en .env si quieres

class CreateEventTool(BaseTool):
    name = "create_event"
    description = "Crea un evento en Google Calendar. Input: JSON con 'summary','start','end','attendees' (opcional)."

    def _run(self, query: str):
        data = json.loads(query)
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('calendar', 'v3', credentials=creds)
        event = {
            "summary": data["summary"],
            "start": {"dateTime": data["start"]},
            "end": {"dateTime": data["end"]},
        }
        if "attendees" in data:
            event["attendees"] = [{"email": e} for e in data["attendees"]]
        created = service.events().insert(calendarId='primary', body=event).execute()
        return f"Evento creado: {created.get('htmlLink')}"

def create_event_tool():
    return CreateEventTool()


