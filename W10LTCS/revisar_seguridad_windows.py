"""Busca indicios en los registros locales de seguridad de Windows."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any


LOGS = (
    ("Security", (4625, 1102, 4720, 4728, 4732, 4756, 4697)),
    ("System", (7045,)),
    ("Microsoft-Windows-Windows Defender/Operational", (1116, 1117)),
)
MAX_EVENTS_PER_LOG = 1000


def read_log(log_name: str, event_ids: tuple[int, ...], days: int) -> dict[str, Any]:
    """Lee eventos recientes con Get-WinEvent; no modifica el equipo."""
    ids = ",".join(str(event_id) for event_id in event_ids)
    script = rf"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$since = (Get-Date).AddDays(-{days})
try {{
    try {{
        $events = @(Get-WinEvent -FilterHashtable @{{ LogName = '{log_name}'; Id = @({ids}); StartTime = $since }} -MaxEvents {MAX_EVENTS_PER_LOG} -ErrorAction Stop)
    }} catch {{
        if ($_.FullyQualifiedErrorId -like 'NoMatchingEventsFound,*') {{
            $events = @()
        }} else {{
            throw
        }}
    }}
    $items = @($events | ForEach-Object {{
        [pscustomobject]@{{
            time = $_.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss zzz')
            id = $_.Id
            provider = $_.ProviderName
            message = $_.Message
        }}
    }})
    [pscustomobject]@{{ log = '{log_name}'; events = $items; error = $null }} | ConvertTo-Json -Compress -Depth 4
}} catch {{
    [pscustomobject]@{{ log = '{log_name}'; events = @(); error = $_.Exception.Message }} | ConvertTo-Json -Compress -Depth 4
}}
"""
    completed = subprocess.run(
        [
            shutil.which("powershell.exe") or "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"PowerShell no pudo consultar el registro {log_name}: {detail}")

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"PowerShell devolvió una respuesta no válida para el registro {log_name}."
        ) from exc

    if not isinstance(result, dict) or not isinstance(result.get("events"), list):
        raise RuntimeError(f"Respuesta inesperada al consultar el registro {log_name}.")
    return result


def describe_event(event_id: int) -> str:
    descriptions = {
        4625: "Inicio de sesión fallido (puede ser un error normal o un intento no autorizado)",
        1102: "Se borró el registro de auditoría de seguridad",
        4720: "Se creó una cuenta de usuario",
        4728: "Se agregó una cuenta a un grupo global de seguridad",
        4732: "Se agregó una cuenta a un grupo local de seguridad",
        4756: "Se agregó una cuenta a un grupo universal de seguridad",
        4697: "Se instaló un servicio",
        7045: "Se instaló un servicio en el sistema",
        1116: "Microsoft Defender detectó una amenaza",
        1117: "Microsoft Defender tomó una acción frente a una amenaza",
    }
    return descriptions.get(event_id, "Evento de seguridad")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Busca indicios en registros locales de Windows (solo lectura)."
    )
    parser.add_argument(
        "--dias",
        type=int,
        default=7,
        help="Cuántos días atrás revisar (1-365; predeterminado: 7).",
    )
    args = parser.parse_args()

    if not 1 <= args.dias <= 365:
        parser.error("--dias debe estar entre 1 y 365.")
    if sys.platform != "win32":
        print("Este programa solo funciona en Windows.", file=sys.stderr)
        return 1

    print(f"Revisión de registros de Windows: últimos {args.dias} días")
    print("Solo lectura. Los resultados son indicios, no una confirmación de ataque.\n")
    found = 0
    had_errors = False

    for log_name, event_ids in LOGS:
        try:
            result = read_log(log_name, event_ids, args.dias)
        except RuntimeError as exc:
            print(f"[ERROR] {log_name}: {exc}")
            had_errors = True
            continue

        if result["error"]:
            print(f"[AVISO] No se pudo leer {log_name}: {result['error']}")
            had_errors = True
            continue

        events = result["events"]
        found += len(events)
        print(f"--- {log_name}: {len(events)} evento(s) ---")
        for event in events:
            message = " ".join(str(event.get("message", "")).split())
            if len(message) > 500:
                message = message[:497] + "..."
            print(
                f"{event.get('time', 'Fecha desconocida')} | "
                f"ID {event.get('id', '?')} | "
                f"{describe_event(int(event.get('id', 0)))}"
            )
            if message:
                print(f"  Detalle: {message}")
        if len(events) == MAX_EVENTS_PER_LOG:
            print(f"  Aviso: se muestran como máximo {MAX_EVENTS_PER_LOG} eventos de este registro.")
        print()

    if found == 0:
        print("No se encontraron eventos coincidentes en los registros que se pudieron leer.")
    print(
        "Importante: los inicios fallidos y otros eventos pueden tener causas legítimas; "
        "la ausencia de eventos no demuestra que el equipo nunca haya sido atacado."
    )
    if had_errors:
        print(
            "Algunos registros no se pudieron leer. Prueba a ejecutar la terminal como "
            "administrador y vuelve a intentarlo."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
