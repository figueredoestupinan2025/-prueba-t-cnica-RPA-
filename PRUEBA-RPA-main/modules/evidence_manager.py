"""
Gestor de evidencias para el proceso RPA
Registra eventos, operaciones de archivos y genera un log consolidado en JSON
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import EVIDENCES_DIR, FileSettings, LOGS_DIR
from utils.logger import setup_logger


@dataclass
class EvidenceEvent:
    timestamp: str
    stage: str
    success: bool
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class FileEvidence:
    timestamp: str
    operation: str
    filepath: str
    exists: bool
    file_size: Optional[int]
    success: bool
    extra: Optional[Dict[str, Any]] = None


class EvidenceManager:
    """Gestor central de evidencias del proceso"""

    def __init__(self):
        self.logger = setup_logger("EvidenceManager")
        # Asegurar directorio de evidencias
        EVIDENCES_DIR.mkdir(parents=True, exist_ok=True)

        self.started_at = datetime.now()
        self.events: List[EvidenceEvent] = []
        self.files: List[FileEvidence] = []

    # Eventos de proceso (pasos, acciones lógicas)
    def capture_process_evidence(self, stage: str, success: bool, metadata: Optional[Dict[str, Any]] = None):
        event = EvidenceEvent(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            stage=stage,
            success=success,
            metadata=metadata or {}
        )
        self.events.append(event)
        self.logger.info(f"EVIDENCE EVENT: {stage} | success={success}", metadata)

    # Operaciones de archivos (Excel, JSON, screenshots, etc.)
    def capture_file_operation(
        self,
        operation: str,
        filepath: str,
        success: bool,
        extra: Optional[Dict[str, Any]] = None
    ):
        try:
            p = Path(filepath)
            exists = p.exists()
            file_size = p.stat().st_size if exists else None
        except Exception:
            exists = False
            file_size = None

        record = FileEvidence(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            operation=operation,
            filepath=str(filepath),
            exists=exists,
            file_size=file_size,
            success=success,
            extra=extra or {}
        )
        self.files.append(record)
        self.logger.info(
            f"EVIDENCE FILE: {operation} | {p.name if 'p' in locals() else filepath} | success={success}",
            {"exists": exists, "file_size": file_size}
        )

    def register_screenshot(self, filepath: str, success: bool = True, extra: Optional[Dict[str, Any]] = None):
        """Atajo para registrar screenshots guardados por otros módulos"""
        self.capture_file_operation("SCREENSHOT", filepath, success, extra)

    def _auto_discover_screenshots(self) -> List[str]:
        """Descubre screenshots en el directorio de evidencias"""
        try:
            return [str(p) for p in EVIDENCES_DIR.glob("*.png")]
        except Exception:
            return []

    def save_evidence_log(self, process_stats: Optional[Dict[str, Any]] = None) -> str:
        """
        Persiste un JSON con el resumen de evidencias del proceso.
        Incluye eventos, operaciones de archivos y metadatos.
        """
        try:
            # Auto registro de screenshots si no se añadieron explícitamente
            for shot in self._auto_discover_screenshots():
                # Evitar duplicados por filepath
                if not any(f.filepath == shot for f in self.files):
                    self.register_screenshot(shot, True)

            finished_at = datetime.now()
            duration_sec = round((finished_at - self.started_at).total_seconds(), 2)

            evidence_doc = {
                "evidence_version": 1,
                "started_at": self.started_at.isoformat(timespec="seconds"),
                "finished_at": finished_at.isoformat(timespec="seconds"),
                "duration_seconds": duration_sec,
                "process_stats": process_stats or {},
                "events": [asdict(e) for e in self.events],
                "files": [asdict(f) for f in self.files],
                "logs_hint": str(LOGS_DIR),
            }

            # Nombre de archivo con timestamp
            ts = datetime.now().strftime(FileSettings.DATETIME_FORMAT)
            filename = f"{FileSettings.EVIDENCE_PREFIX}{ts}.json"
            out_path = EVIDENCES_DIR / filename

            with open(out_path, "w", encoding=FileSettings.DEFAULT_ENCODING) as f:
                json.dump(evidence_doc, f, ensure_ascii=FileSettings.JSON_ENSURE_ASCII, indent=FileSettings.JSON_INDENT)

            self.logger.info(f"✅ Evidencias registradas: {out_path}")
            return str(out_path)
        except Exception as e:
            self.logger.error(f"Error guardando log de evidencias: {e}")
            return ""


# Factory para inicializar

def initialize_evidence_manager() -> EvidenceManager:
    return EvidenceManager()
