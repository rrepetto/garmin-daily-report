import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from garminconnect import Garmin


# Fecha de ayer en Argentina
timezone = ZoneInfo("America/Argentina/Buenos_Aires")
day = (datetime.now(timezone) - timedelta(days=1)).date()
date_str = day.isoformat()


def duration(seconds):
    if seconds is None:
        return "Sin datos"

    minutes = round(seconds / 60)
    return f"{minutes // 60} h {minutes % 60} min"


# Conectar a Garmin Connect
garmin = Garmin(
    os.environ["GARMIN_EMAIL"],
    os.environ["GARMIN_PASSWORD"]
)

garmin.login()
print("Login Garmin completado correctamente")

# Verificar acceso a la API
stats = garmin.get_stats(date_str)
print("Consulta de estadísticas completada")
print("Fecha consultada:", date_str)

# Consultar sueño
# Buscar datos de sueño en los últimos 3 días
for offset in range(1, 4):
    test_date = (
        datetime.now(timezone) - timedelta(days=offset)
    ).date().isoformat()

    data = garmin.get_sleep_data(test_date)
    sleep = (data or {}).get("dailySleepDTO") or {}

    print(f"\nFecha: {test_date}")
    print("Sueño total:", sleep.get("sleepTimeSeconds"))
    print("Profundo:", sleep.get("deepSleepSeconds"))
    print("Ligero:", sleep.get("lightSleepSeconds"))
    print("REM:", sleep.get("remSleepSeconds"))
    print("Campos disponibles:", list(sleep.keys()))

#if not sleep.get("sleepTimeSeconds"):
#    raise RuntimeError(
#        f"No hay información de sueño para {date_str}"
#    )

# Generar informe Markdown
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

# Guardar informe
Path("reports").mkdir(exist_ok=True)
file = Path(f"reports/{date_str}.md")
file.write_text(report, encoding="utf-8")

print(f"Informe generado: {file}")
