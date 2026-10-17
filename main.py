import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from garminconnect import Garmin


TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")


def duration(seconds):
    if seconds is None:
        return "Sin datos"

    minutes = round(seconds / 60)
    return f"{minutes // 60} h {minutes % 60} min"


def get_latest_sleep(garmin):
    today = datetime.now(TIMEZONE).date()

    for offset in range(1, 4):
        day = today - timedelta(days=offset)
        date_str = day.isoformat()

        data = garmin.get_sleep_data(date_str)
        sleep = (data or {}).get("dailySleepDTO") or {}

        if sleep.get("sleepTimeSeconds"):
            return date_str, sleep

    raise RuntimeError("No se encontraron datos de sueño")


def main():
    garmin = Garmin(
        os.environ["GARMIN_EMAIL"],
        os.environ["GARMIN_PASSWORD"]
    )
    garmin.login()

    date_str, sleep = get_latest_sleep(garmin)

    report = f"""# Garmin — Sueño del {date_str}

## Resumen

| Métrica | Valor |
|---|---|
| Sueño total | {duration(sleep.get('sleepTimeSeconds'))} |
| Sueño profundo | {duration(sleep.get('deepSleepSeconds'))} |
| Sueño ligero | {duration(sleep.get('lightSleepSeconds'))} |
| Sueño REM | {duration(sleep.get('remSleepSeconds'))} |
| Tiempo despierto | {duration(sleep.get('awakeSleepSeconds'))} |

---
Generado automáticamente desde Garmin Connect.
"""

    Path("reports").mkdir(exist_ok=True)
    file = Path(f"reports/{date_str}.md")

    if file.exists():
        print(f"El informe ya existe: {file}")
        return

    file.write_text(report, encoding="utf-8")

    print(f"Informe generado: {file}")


if __name__ == "__main__":
    main()
