import os
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from garminconnect import Garmin

TZ = ZoneInfo("America/Argentina/Buenos_Aires")
day = (datetime.now(TZ) - timedelta(days=1)).date()
date_str = day.isoformat()

# Autenticación Garmin
garmin = Garmin(
    os.environ["GARMIN_EMAIL"],
    os.environ["GARMIN_PASSWORD"]
)
garmin.login()

# Obtener sueño
data = garmin.get_sleep_data(date_str)
sleep = (data or {}).get("dailySleepDTO") or {}

if not sleep.get("sleepTimeSeconds"):
    raise RuntimeError(
        f"No hay datos de sueño para {date_str}. "
        "Verificar sincronización del reloj."
    )

def duration(seconds):
    if seconds is None:
        return "Sin datos"
    minutes = round(seconds / 60)
    return f"{minutes // 60} h {minutes % 60} min"

# Preparar informe
report = f"""
Resumen de sueño — {date_str}

Sueño total: {duration(sleep.get('sleepTimeSeconds'))}
Sueño profundo: {duration(sleep.get('deepSleepSeconds'))}
Sueño ligero: {duration(sleep.get('lightSleepSeconds'))}
Sueño REM: {duration(sleep.get('remSleepSeconds'))}
Tiempo despierto: {duration(sleep.get('awakeSleepSeconds'))}

Datos obtenidos de Garmin Connect.
"""

# Enviar email
message = EmailMessage()
message["Subject"] = f"Garmin - Sueño {date_str}"
message["From"] = os.environ["SMTP_USER"]
message["To"] = os.environ["REPORT_EMAIL"]
message.set_content(report)

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(
        os.environ["SMTP_USER"],
        os.environ["SMTP_PASSWORD"]
    )
    smtp.send_message(message)

print(f"Informe enviado para {date_str}")
