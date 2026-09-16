from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.analyzer.scanner import scan_repository

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CodeScope",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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