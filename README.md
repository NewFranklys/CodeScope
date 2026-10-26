# CodeScope

> Understand the shape of your codebase without uploading it anywhere.

CodeScope is a **local-first repository intelligence tool**. Point it at a folder on your machine and it builds a compact view of the project: languages, source lines, large files, maintenance markers, dependency manifests, Git state and likely maintenance hotspots.

## v1.0

CodeScope v1 focuses on fast, useful repository inspection without indexing source code in a remote service.

### What it shows

- Repository, file, directory and source-line statistics
- Language distribution by files and lines
- Largest recognized source files
- Searchable local project explorer
- `TODO`, `FIXME`, `HACK` and `XXX` markers with file and line number
- Dependency-manifest discovery with dependency counts where supported
- Git branch, commit count, tracked files and working-tree changes
- Maintenance hotspots based on file size plus maintenance markers
- Local-only API and UI

### Supported language detection

Python, JavaScript, TypeScript, Java, C#, C/C++, Go, Rust, Ruby, PHP, Swift, Kotlin, HTML, CSS/SCSS/Sass/Less, SQL, Shell, PowerShell, Markdown/MDX, JSON, YAML, TOML, XML, Vue, Svelte, Dart, Lua, R and common special files such as Dockerfile and Makefile.

## Architecture

```text
CodeScope/
├── backend/
│   ├── app/
│   │   ├── analyzer/
│   │   │   ├── ignores.py
│   │   │   ├── models.py
│   │   │   └── scanner.py
│   │   └── main.py
│   └── tests/
└── frontend/
    └── src/
        ├── App.tsx
        ├── App.css
        └── index.css
```

The backend is a small FastAPI service. The frontend is React + TypeScript + Vite. The browser sends only the local path to the local FastAPI process; CodeScope does not need a cloud backend.

## Run locally

### 1. Backend

```bash
cd backend
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Install and run:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000` and FastAPI docs at `http://127.0.0.1:8000/docs`.

### 2. Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.

If your API runs elsewhere, set `VITE_API_URL` before starting the frontend.

## Tests

Backend:

```bash
cd backend
pytest -q
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

GitHub Actions runs the backend tests and frontend lint/build checks on pushes and pull requests.

## Local-first limits

To keep scans responsive, CodeScope ignores common generated/vendor folders such as `.git`, `node_modules`, virtual environments, build outputs, caches and Rust `target`. Individual text files larger than 5 MB are not read for line/TODO analysis. The project explorer returns up to 2,000 paths and TODO results are capped at 500.

## Hotspot score

The v1 hotspot score is intentionally simple and explainable:

```text
score = source lines + (maintenance markers × 40)
```

It is a prioritization hint, not a complexity metric or a code-quality verdict.

## Privacy

**Your source stays on your machine.** CodeScope scans local files through the local backend and does not upload repository contents to a remote analysis service.
