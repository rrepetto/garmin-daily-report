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

def percentage(seconds, total):
    if seconds is None or not total:
        return "Sin datos"

    return f"{seconds / total * 100:.0f}%"

def status(value, minimum, maximum, tolerance):
    if value is None:
        return "⚪"

    if value > maximum:
        return "⚪"

    if value >= minimum:
        return "🟢 ✅"

    if value >= minimum - tolerance:
        return "🟡 ⚠️"

    return "🔴 ❌"


def phase_status(seconds, total, minimum, maximum):
    if seconds is None or not total:
        return "⚪"

    pct = seconds / total * 100
    return status(pct, minimum, maximum, 5)

def get_latest_sleep(garmin):
    today = datetime.now(TIMEZONE).date()

    for offset in range(0, 4):
        day = today - timedelta(days=offset)
        date_str = day.isoformat()

        data = garmin.get_sleep_data(date_str)
        sleep = (data or {}).get("dailySleepDTO") or {}

        print(
            f"Fecha: {date_str}, "
            f"Sueño: {sleep.get('sleepTimeSeconds')}, "
            f"CalendarDate: {sleep.get('calendarDate')}"
        )

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

    total = sleep.get("sleepTimeSeconds")

    deep = sleep.get("deepSleepSeconds")
    light = sleep.get("lightSleepSeconds")
    rem = sleep.get("remSleepSeconds")
    awake = sleep.get("awakeSleepSeconds")

    total_status = status(
        total / 3600 if total is not None else None,
        7, 9, 1
    )

    report = f"""# Garmin — Sueño del {date_str}

## Resumen

| Métrica | Duración | Estado | % | Referencia adultos |
|---|---|---|---|---|
| Sueño total | {duration(total)} | {total_status} | 100% | 7–9 h |
| Sueño profundo | {duration(deep)} | {phase_status(deep, total, 15, 25)} | {percentage(deep, total)} | 15–25% |
| Sueño ligero | {duration(light)} | {phase_status(light, total, 50, 60)} | {percentage(light, total)} | ~50–60% |
| Sueño REM | {duration(rem)} | {phase_status(rem, total, 20, 25)} | {percentage(rem, total)} | 20–25% |
| Tiempo despierto | {duration(awake)} | ⚪ | — | Variable |

---

**Estados:** 🟢 En rango · 🟡 Cerca del rango · 🔴 Fuera del rango · ⚪ Sin evaluación.

*Referencias orientativas. Los porcentajes de fases no son
umbrales médicos y Garmin proporciona estimaciones.*

Generado automáticamente desde Garmin Connect.
"""

    Path("reports").mkdir(exist_ok=True)
    file = Path(f"reports/{date_str}.md")

    if not file.exists():
        file.write_text(report, encoding="utf-8")
        print(f"Informe generado: {file}")
    else:
        print(f"El informe ya existe: {file}")

    # Generar índice con todos los reportes
    reports = sorted(
        Path("reports").glob("????-??-??.md"),
        reverse=True
    )

    now = datetime.now(TIMEZONE)
    last_run = now.strftime("%d/%m/%Y a las %H:%M")

    index = f"""# Garmin — Reportes de sueño

**Última consulta exitosa a Garmin:** {last_run} (Argentina)

## Reportes

"""

    for path in reports:
        index += f"- [{path.stem}](reports/{path.name})\n"

    Path("index.md").write_text(index, encoding="utf-8")

    print(f"Índice actualizado con {len(reports)} reportes")

if __name__ == "__main__":
    main()
