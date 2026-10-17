
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from garminconnect import Garmin


TIMEZONE = ZoneInfo("America/Argentina/Buenos_Aires")
DAYS_BACK = 7


def duration(seconds):
    if seconds is None:
        return "Sin datos"

    minutes = round(seconds / 60)
    return f"{minutes // 60} h {minutes % 60:02d} min ({minutes} min)"


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


def phase_status(seconds, minimum_minutes, maximum_minutes):
    if seconds is None:
        return "⚪"

    return status(
        seconds / 60,
        minimum_minutes,
        maximum_minutes,
        minimum_minutes * 0.20
    )


def generate_report(date_str, sleep):
    total = sleep.get("sleepTimeSeconds")

    deep = sleep.get("deepSleepSeconds")
    light = sleep.get("lightSleepSeconds")
    rem = sleep.get("remSleepSeconds")
    awake = sleep.get("awakeSleepSeconds")

    total_status = status(
        total / 3600 if total is not None else None,
        7, 9, 1
    )

    return f"""# Garmin — Sueño del {date_str}

## Resumen

| Métrica | Duración | Estado | % | Referencia adultos |
|---|---|---|---|---|
| Sueño total | {duration(total)} | {total_status} | 100% | 7–9 h |
| Sueño profundo | {duration(deep)} | {phase_status(deep, 72, 120)} | {percentage(deep, total)} | 72–120 min |
| Sueño ligero | {duration(light)} | ⚪ | {percentage(light, total)} | Sin objetivo |
| Sueño REM | {duration(rem)} | {phase_status(rem, 96, 120)} | {percentage(rem, total)} | 96–120 min |
| Tiempo despierto | {duration(awake)} | ⚪ | — | Variable |

---

**Estados:** 🟢 Objetivo alcanzado · 🟡 Hasta 20% por debajo · 🔴 Más de 20% por debajo · ⚪ Sin evaluación o por encima de la referencia.

*Los objetivos de REM y sueño profundo son referencias personalizadas calculadas a partir de 8 horas de sueño, no mínimos médicos validados.*

*Garmin proporciona estimaciones de las fases de sueño.*

Generado automáticamente desde Garmin Connect.
"""


def main():
    garmin = Garmin(
        os.environ["GARMIN_EMAIL"],
        os.environ["GARMIN_PASSWORD"]
    )
    garmin.login()

    today = datetime.now(TIMEZONE).date()
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    generated = 0

    # Consultar hoy y los 7 días anteriores
    for offset in range(DAYS_BACK + 1):
        day = today - timedelta(days=offset)
        date_str = day.isoformat()
        file = reports_dir / f"{date_str}.md"

        if file.exists():
            print(f"{date_str}: informe existente")
            continue

        data = garmin.get_sleep_data(date_str)
        sleep = (data or {}).get("dailySleepDTO") or {}

        if not sleep.get("sleepTimeSeconds"):
            print(f"{date_str}: sin datos de sueño")
            continue

        report = generate_report(date_str, sleep)
        file.write_text(report, encoding="utf-8")

        print(f"{date_str}: informe generado")
        generated += 1

    # Generar índice con todos los reportes
    reports = sorted(
        reports_dir.glob("????-??-??.md"),
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

    print(f"Informes nuevos: {generated}")
    print(f"Informes totales: {len(reports)}")


if __name__ == "__main__":
    main()
