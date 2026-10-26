from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.analyzer.scanner import scan_repository


app = FastAPI(
    title="CodeScope",
    description="Local-first repository intelligence API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class AnalyzeRequest(BaseModel):
    path: str = Field(min_length=1, max_length=4096)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "name": "CodeScope",
        "version": "1.0.0",
    }


@app.post("/api/analyze")
def analyze_repository(request: AnalyzeRequest):
    try:
        analysis = scan_repository(request.path.strip())
        return asdict(analysis)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except NotADirectoryError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to read repository: {error}",
        ) from error
