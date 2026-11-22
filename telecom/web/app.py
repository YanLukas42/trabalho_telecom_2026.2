"""FastAPI Backend para o Trabalho Telecom 2026.2.
Fornece API REST e serve a interface web para diarização, benchmarks e análise de métricas.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from telecom.diarization.models import Diarizer
from telecom.experiments import MATRICES
from telecom.settings import (
    BENCHMARK_OUTPUT_DIR,
    DIARIZATION_OUTPUT_DIR,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    HF_TOKEN,
    INPUT_DIR,
    MEDIA_EXTENSIONS,
    OUTPUT_DIR,
    PRICE_INPUT_USD_PER_M,
    PRICE_OUTPUT_USD_PER_M,
    ROOT_DIR,
    USD_TO_BRL,
)

logger = logging.getLogger("telecom.web")

app = FastAPI(
    title="Telecom 2026.2 — Áudio & Diarização com Gemini",
    description="Interface de pesquisa em otimização de áudio para transcrição e diarização",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Armazenamento em memória de tarefas em execução
TASKS: dict[str, dict[str, Any]] = {}


class LogCaptureHandler(logging.Handler):
    """Captura logs em tempo real para streaming na interface web."""

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id

    def emit(self, record: logging.LogRecord):
        if self.task_id in TASKS:
            msg = self.format(record)
            TASKS[self.task_id]["logs"].append(
                {
                    "time": time.strftime("%H:%M:%S"),
                    "level": record.levelname,
                    "message": msg,
                }
            )


# Modelos Pydantic para requisições
class DiarizeRequest(BaseModel):
    file_name: str
    engine: str = "gemini"
    codec: str = "opus"
    vad: bool = True
    review: bool = False
    model: str | None = None
    whisper_model: str = "small"
    language: str = "pt"
    device: str = "cpu"
    num_speakers: int | None = None


class RenameSpeakerRequest(BaseModel):
    report_file: str
    old_speaker: str
    new_speaker: str


class BenchmarkRequest(BaseModel):
    suite: str
    file_name: str
    dry_run: bool = False
    model: str | None = None


# Helpers
def _has_binary(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _find_media_file(filename: str) -> Path | None:
    """Busca um arquivo de mídia em input/ ou nos diretórios de saída."""
    candidates = [
        INPUT_DIR / filename,
        DIARIZATION_OUTPUT_DIR / "audio" / filename,
        OUTPUT_DIR / filename,
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    # Busca por stem
    stem = Path(filename).stem
    for folder in [INPUT_DIR, DIARIZATION_OUTPUT_DIR / "audio"]:
        if folder.exists():
            for p in folder.iterdir():
                if p.stem == stem and p.suffix.lower() in MEDIA_EXTENSIONS:
                    return p
    return None


@app.get("/api/status")
def get_status() -> dict[str, Any]:
    """Retorna o estado do ambiente, ferramentas instaladas e chaves de API."""
    return {
        "has_gemini_key": bool(GEMINI_API_KEY and GEMINI_API_KEY.strip()),
        "gemini_model": GEMINI_MODEL,
        "has_hf_token": bool(HF_TOKEN and HF_TOKEN.strip()),
        "has_ffmpeg": _has_binary("ffmpeg"),
        "has_ffprobe": _has_binary("ffprobe"),
        "input_dir": str(INPUT_DIR),
        "output_dir": str(OUTPUT_DIR),
        "rates": {
            "price_input_usd_per_m": PRICE_INPUT_USD_PER_M,
            "price_output_usd_per_m": PRICE_OUTPUT_USD_PER_M,
            "usd_to_brl": USD_TO_BRL,
        },
        "models": [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
    }


@app.get("/api/reports")
def list_reports() -> list[dict[str, Any]]:
    """Lista todos os relatórios disponíveis (diarização e benchmark)."""
    reports: list[dict[str, Any]] = []
    reports_dir = DIARIZATION_OUTPUT_DIR / "reports"
    if reports_dir.exists():
        for file in sorted(reports_dir.glob("*.json"), key=os.path.getmtime, reverse=True):
            if "palavra_por_palavra" in file.name:
                continue
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                original_file = data.get("arquivo", "")
                media_path = _find_media_file(original_file)

                # Verifica se há arquivo de alinhamento palavra por palavra correspondente
                words_filename = file.name.replace("_diarizacao_pydantic", "_palavra_por_palavra")
                has_words = (reports_dir / words_filename).exists()

                # Verifica se há markdown
                md_filename = file.stem + ".md"
                has_md = (reports_dir / md_filename).exists()

                reports.append(
                    {
                        "id": file.name,
                        "type": "diarizacao",
                        "arquivo": original_file,
                        "codec": data.get("codec", "desconhecido"),
                        "vad_aplicado": data.get("vad_aplicado", False),
                        "duracao_original_segundos": data.get("duracao_original_segundos", 0.0),
                        "duracao_compactada_segundos": data.get("duracao_compactada_segundos", 0.0),
                        "economia_silencio_pct": data.get("economia_silencio_pct", 0.0),
                        "custo_estimado": data.get("custo_estimado", {}),
                        "metricas_tokens": data.get("metricas_tokens", {}),
                        "total_turnos_fala": data.get("total_turnos_fala", len(data.get("segmentos", []))),
                        "tempo_execucao_total_segundos": data.get("tempo_execucao_total_segundos", 0.0),
                        "tempo_processamento_nuvem_segundos": data.get("tempo_processamento_nuvem_segundos", 0.0),
                        "has_words": has_words,
                        "words_file": words_filename if has_words else None,
                        "has_md": has_md,
                        "has_media": media_path is not None,
                        "media_url": f"/api/media/{media_path.name}" if media_path else None,
                        "mtime": os.path.getmtime(file),
                    }
                )
            except Exception as e:
                logger.warning("Falha ao ler relatório %s: %s", file.name, e)

    return reports


@app.get("/api/reports/{filename}")
def get_report(filename: str) -> dict[str, Any]:
    """Retorna o conteúdo completo de um relatório JSON de diarização."""
    file_path = DIARIZATION_OUTPUT_DIR / "reports" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        original_file = data.get("arquivo", "")
        media_path = _find_media_file(original_file)
        data["media_url"] = f"/api/media/{media_path.name}" if media_path else None

        # Procura palavras correspondentes
        words_filename = filename.replace("_diarizacao_pydantic", "_palavra_por_palavra")
        words_path = DIARIZATION_OUTPUT_DIR / "reports" / words_filename
        if words_path.exists():
            data["words_filename"] = words_filename

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler relatório: {e}")


@app.get("/api/reports/{filename}/markdown")
def get_report_markdown(filename: str):
    """Retorna a versão Markdown do relatório."""
    stem = Path(filename).stem
    md_path = DIARIZATION_OUTPUT_DIR / "reports" / f"{stem}.md"
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="Markdown correspondente não encontrado")
    return {"markdown": md_path.read_text(encoding="utf-8")}


@app.get("/api/reports/{filename}/words")
def get_word_alignment(filename: str):
    """Retorna o alinhamento palavra por palavra de um relatório."""
    words_filename = filename.replace("_diarizacao_pydantic", "_palavra_por_palavra")
    words_path = DIARIZATION_OUTPUT_DIR / "reports" / words_filename
    if not words_path.exists():
        raise HTTPException(status_code=404, detail="Alinhamento palavra por palavra não encontrado")

    try:
        return json.loads(words_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao ler alinhamento de palavras: {e}")


@app.put("/api/reports/{filename}/rename-speaker")
def rename_speaker(req: RenameSpeakerRequest):
    """Renomeia um falante no relatório JSON e salva as alterações."""
    file_path = DIARIZATION_OUTPUT_DIR / "reports" / req.report_file
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        count = 0
        for seg in data.get("segmentos", []):
            if seg.get("quemfala") == req.old_speaker:
                seg["quemfala"] = req.new_speaker
                count += 1
            if seg.get("falante_identificado") == req.old_speaker:
                seg["falante_identificado"] = req.new_speaker

        file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Atualiza também arquivo de palavras, se existir
        words_filename = req.report_file.replace("_diarizacao_pydantic", "_palavra_por_palavra")
        words_path = DIARIZATION_OUTPUT_DIR / "reports" / words_filename
        if words_path.exists():
            wdata = json.loads(words_path.read_text(encoding="utf-8"))
            for w in wdata.get("palavras", []):
                if w.get("quemfala") == req.old_speaker:
                    w["quemfala"] = req.new_speaker
            words_path.write_text(json.dumps(wdata, indent=2, ensure_ascii=False), encoding="utf-8")

        return {"status": "ok", "substituicoes": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao renomear falante: {e}")


@app.get("/api/inputs")
def list_inputs() -> list[dict[str, Any]]:
    """Lista os arquivos de mídia em input/."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for f in sorted(INPUT_DIR.iterdir()):
        if f.is_file() and f.suffix.lower() in MEDIA_EXTENSIONS:
            files.append(
                {
                    "name": f.name,
                    "size_bytes": f.stat().st_size,
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "suffix": f.suffix.lower(),
                    "mtime": f.stat().st_mtime,
                }
            )
    return files


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Faz upload de um arquivo de áudio ou vídeo para input/."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = INPUT_DIR / file.filename
    try:
        with dest_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {
            "status": "ok",
            "filename": file.filename,
            "size_bytes": dest_path.stat().st_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {e}")


@app.get("/api/media/{filename}")
def stream_media(filename: str):
    """Transmite um arquivo de áudio ou vídeo com suporte a Range requests."""
    media_path = _find_media_file(filename)
    if not media_path:
        raise HTTPException(status_code=404, detail="Arquivo de mídia não encontrado")

    mime_types = {
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".opus": "audio/ogg",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".webm": "video/webm",
    }
    media_type = mime_types.get(media_path.suffix.lower(), "application/octet-stream")
    return FileResponse(media_path, media_type=media_type)


def _run_diarize_task(task_id: str, req: DiarizeRequest):
    """Executa a pipeline de diarização em background."""
    handler = LogCaptureHandler(task_id)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    try:
        TASKS[task_id]["status"] = "running"
        TASKS[task_id]["progress"] = 10

        media_path = INPUT_DIR / req.file_name
        if not media_path.exists():
            media_path = _find_media_file(req.file_name)
        if not media_path or not media_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {req.file_name}")

        TASKS[task_id]["progress"] = 25
        logger.info("Iniciando diarização de: %s (Engine: %s, Codec: %s, VAD: %s)",
                    media_path.name, req.engine, req.codec, req.vad)

        # Constrói o diarizador
        if req.engine == "gemini":
            from telecom.asr.gemini import GeminiClient
            from telecom.diarization.transcriber import GeminiDiarizer

            client = GeminiClient(model=req.model)
            diarizer = GeminiDiarizer(client)
        else:
            if not HF_TOKEN:
                raise ValueError("HF_TOKEN não configurado para uso do pyannote")
            from telecom.diarization.pyannote_whisper import build_local_diarizer

            diarizer = build_local_diarizer(
                hf_token=HF_TOKEN,
                whisper_model=req.whisper_model,
                device=req.device,
                language=req.language,
                num_speakers=req.num_speakers,
            )

        TASKS[task_id]["progress"] = 45

        reviewer = None
        if req.review:
            from telecom.asr.gemini import GeminiClient
            from telecom.diarization.review import GeminiReviewer

            reviewer = GeminiReviewer(GeminiClient(model=req.model))

        from telecom.diarization.pipeline import DiarizationOptions, DiarizationPipeline

        pipeline = DiarizationPipeline(
            diarizer=diarizer,
            options=DiarizationOptions(codec=req.codec, compact_silence=req.vad),
            reviewer=reviewer,
        )

        TASKS[task_id]["progress"] = 65
        outputs = pipeline.run(media_path)

        TASKS[task_id]["progress"] = 100
        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["result"] = {
            "report_json": outputs.report_json.name,
            "report_md": outputs.report_md.name,
            "words_json": outputs.words_json.name,
            "payload": outputs.payload,
        }
        logger.info("Diarização concluída com sucesso! Relatório gerado em: %s", outputs.report_json.name)

    except Exception as e:
        logger.exception("Erro durante diarização: %s", e)
        TASKS[task_id]["status"] = "error"
        TASKS[task_id]["error"] = str(e)
    finally:
        root_logger.removeHandler(handler)


@app.post("/api/diarize")
def start_diarization(req: DiarizeRequest, bg_tasks: BackgroundTasks):
    """Inicia a execução do diarizador em segundo plano."""
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "id": task_id,
        "type": "diarize",
        "file_name": req.file_name,
        "status": "pending",
        "progress": 0,
        "logs": [],
        "created_at": time.time(),
    }
    bg_tasks.add_task(_run_diarize_task, task_id, req)
    return {"task_id": task_id, "status": "pending"}


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    """Verifica o status e progresso de uma tarefa assíncrona."""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return TASKS[task_id]


@app.get("/api/tasks/{task_id}/events")
async def task_events(task_id: str):
    """Streaming SSE (Server-Sent Events) dos logs e status da tarefa."""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")

    async def event_generator() -> AsyncGenerator[str, None]:
        last_log_idx = 0
        while True:
            task = TASKS.get(task_id)
            if not task:
                break

            current_logs = task["logs"]
            if len(current_logs) > last_log_idx:
                for log_entry in current_logs[last_log_idx:]:
                    yield f"event: log\ndata: {json.dumps(log_entry, ensure_ascii=False)}\n\n"
                last_log_idx = len(current_logs)

            status_payload = {
                "status": task["status"],
                "progress": task["progress"],
                "error": task.get("error"),
                "result": task.get("result"),
            }
            yield f"event: status\ndata: {json.dumps(status_payload, ensure_ascii=False)}\n\n"

            if task["status"] in ("completed", "error"):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/benchmark/matrices")
def get_benchmark_matrices():
    """Retorna as matrizes de experimentos definidas em telecom.experiments."""
    matrices_summary = {}
    for name, treatments in MATRICES.items():
        matrices_summary[name] = [
            {
                "id": t.id,
                "label": t.label,
                "codec": t.codec,
                "bitrate": t.bitrate,
                "sample_rate": t.sample_rate,
                "channels": t.channels,
                "compact_silence": t.compact_silence,
                "filters": list(t.filters),
            }
            for t in treatments
        ]
    return matrices_summary


# Serve arquivos estáticos da interface web
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    """Entrega a Single-Page Application (SPA)."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(index_file.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Frontend em carregamento...</h1>")
