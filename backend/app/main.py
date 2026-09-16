from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.analyzer.scanner import scan_repository


app = FastAPI(
    title="CodeScope",
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    path: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "name": "CodeScope",
        "version": "0.1.0",
    }


@app.post("/api/analyze")
def analyze_repository(request: AnalyzeRequest):
    try:
        analysis = scan_repository(request.path)

        return asdict(analysis)

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except NotADirectoryError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error