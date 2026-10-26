import { useMemo, useState, type ChangeEvent, type FormEvent } from "react";
import "./App.css";

type FileAnalysis = {
  path: string;
  lines: number;
  language: string;
  size_bytes: number;
  todos: number;
};

type TodoItem = {
  path: string;
  line: number;
  tag: string;
  text: string;
};

type DependencyManifest = {
  path: string;
  kind: string;
  dependencies: number | null;
};

type GitInsights = {
  branch: string | null;
  commits: number;
  changed_files: number;
  tracked_files: number;
};

type Hotspot = {
  path: string;
  language: string;
  lines: number;
  todos: number;
  score: number;
};

type RepositoryAnalysis = {
  name: string;
  path: string;
  files: number;
  analyzed_files: number;
  directories: number;
  lines: number;
  size_bytes: number;
  languages: Record<string, number>;
  language_lines: Record<string, number>;
  largest_files: FileAnalysis[];
  todos: TodoItem[];
  dependency_manifests: DependencyManifest[];
  git: GitInsights | null;
  hotspots: Hotspot[];
  files_index: string[];
  files_index_truncated: boolean;
};

type Tab = "overview" | "files" | "todos" | "git";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

function formatNumber(value: number) {
  return new Intl.NumberFormat().format(value);
}

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  const units = ["KB", "MB", "GB"];
  let current = value / 1024;
  let unit = units[0];

  for (let index = 1; index < units.length && current >= 1024; index += 1) {
    current /= 1024;
    unit = units[index];
  }

  return `${current.toFixed(current >= 10 ? 0 : 1)} ${unit}`;
}

function App() {
  const [repositoryPath, setRepositoryPath] = useState("");
  const [analysis, setAnalysis] = useState<RepositoryAnalysis | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [fileQuery, setFileQuery] = useState("");

  const filteredFiles = useMemo(() => {
    if (!analysis) return [];
    const query = fileQuery.trim().toLowerCase();
    if (!query) return analysis.files_index;
    return analysis.files_index.filter((path) => path.toLowerCase().includes(query));
  }, [analysis, fileQuery]);

  async function handleAnalyze(event: FormEvent) {
    event.preventDefault();
    const path = repositoryPath.trim();
    if (!path) return;

    setLoading(true);
    setError("");
    setAnalysis(null);
    setActiveTab("overview");
    setFileQuery("");

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "Unable to analyze repository.");
      }

      setAnalysis(data as RepositoryAnalysis);
    } catch (caughtError) {
      if (caughtError instanceof TypeError) {
        setError("CodeScope backend is offline. Start the API on port 8000 and try again.");
      } else if (caughtError instanceof Error) {
        setError(caughtError.message);
      } else {
        setError("Something went wrong while analyzing the repository.");
      }
    } finally {
      setLoading(false);
    }
  }

  const maxLanguageLines = analysis
    ? Math.max(...Object.values(analysis.language_lines), 1)
    : 1;

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="CodeScope home">
          <span className="brand-mark">C</span>
          <span>CodeScope</span>
        </a>
        <span className="version">v1.0</span>
      </header>

      <section className="intro" id="top">
        <p className="kicker">LOCAL REPOSITORY INTELLIGENCE</p>
        <h1>See the shape of your code.</h1>
        <p className="intro-copy">
          Scan a repository locally to understand its languages, size, maintenance hotspots,
          TODOs, dependency manifests and Git state.
        </p>

        <form className="analyze-form" onSubmit={handleAnalyze}>
          <label htmlFor="repository-path">Repository path</label>
          <div className="input-row">
            <input
              id="repository-path"
              type="text"
              placeholder="C:\\dev\\my-project"
              value={repositoryPath}
              onChange={(event: ChangeEvent<HTMLInputElement>) => setRepositoryPath(event.target.value)}
              autoComplete="off"
            />
            <button type="submit" disabled={loading || !repositoryPath.trim()}>
              {loading ? "Scanning…" : "Analyze"}
            </button>
          </div>
        </form>

        {error && <div className="error-box">{error}</div>}
      </section>

      {analysis && (
        <section className="workspace" aria-live="polite">
          <div className="repo-header">
            <div>
              <p className="section-label">REPOSITORY</p>
              <h2>{analysis.name}</h2>
              <p className="repo-path">{analysis.path}</p>
            </div>
            <div className="repo-status">
              <span className="status-dot" />
              Scan complete
            </div>
          </div>

          <div className="summary-grid">
            <article className="metric-card">
              <span>Files</span>
              <strong>{formatNumber(analysis.files)}</strong>
              <small>{formatNumber(analysis.analyzed_files)} recognized</small>
            </article>
            <article className="metric-card">
              <span>Lines</span>
              <strong>{formatNumber(analysis.lines)}</strong>
              <small>text source lines</small>
            </article>
            <article className="metric-card">
              <span>Languages</span>
              <strong>{Object.keys(analysis.languages).length}</strong>
              <small>{analysis.directories} directories</small>
            </article>
            <article className="metric-card">
              <span>Size</span>
              <strong>{formatBytes(analysis.size_bytes)}</strong>
              <small>excluding ignored folders</small>
            </article>
          </div>

          <nav className="tabs" aria-label="Analysis sections">
            {(["overview", "files", "todos", "git"] as Tab[]).map((tab) => (
              <button
                className={activeTab === tab ? "tab active" : "tab"}
                key={tab}
                type="button"
                onClick={() => setActiveTab(tab)}
              >
                {tab === "overview" && "Overview"}
                {tab === "files" && `Files (${analysis.files})`}
                {tab === "todos" && `TODOs (${analysis.todos.length})`}
                {tab === "git" && "Git & deps"}
              </button>
            ))}
          </nav>

          {activeTab === "overview" && (
            <div className="panel-grid">
              <article className="panel">
                <div className="panel-heading">
                  <div>
                    <p className="section-label">LANGUAGES</p>
                    <h3>Code composition</h3>
                  </div>
                  <span className="muted">by lines</span>
                </div>

                <div className="language-list">
                  {Object.entries(analysis.language_lines).map(([language, lines]) => (
                    <div className="language-item" key={language}>
                      <div className="language-meta">
                        <strong>{language}</strong>
                        <span>{formatNumber(lines)} lines · {analysis.languages[language]} files</span>
                      </div>
                      <div className="bar-track" aria-hidden="true">
                        <span style={{ width: `${Math.max((lines / maxLanguageLines) * 100, 2)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </article>

              <article className="panel">
                <div className="panel-heading">
                  <div>
                    <p className="section-label">HOTSPOTS</p>
                    <h3>Maintenance pressure</h3>
                  </div>
                  <span className="muted">size + markers</span>
                </div>

                <div className="ranked-list">
                  {analysis.hotspots.length ? analysis.hotspots.map((file, index) => (
                    <div className="ranked-row" key={file.path}>
                      <span className="rank">{String(index + 1).padStart(2, "0")}</span>
                      <div className="ranked-main">
                        <strong title={file.path}>{file.path}</strong>
                        <span>{file.language} · {file.lines} lines · {file.todos} markers</span>
                      </div>
                      <span className="score">{file.score}</span>
                    </div>
                  )) : <p className="empty-state">No source hotspots found.</p>}
                </div>
              </article>

              <article className="panel full-width">
                <div className="panel-heading">
                  <div>
                    <p className="section-label">LARGEST FILES</p>
                    <h3>Where the code lives</h3>
                  </div>
                </div>

                <div className="table-list">
                  {analysis.largest_files.map((file) => (
                    <div className="table-row" key={file.path}>
                      <div>
                        <strong>{file.path}</strong>
                        <span>{file.language}</span>
                      </div>
                      <span>{formatBytes(file.size_bytes)}</span>
                      <span>{formatNumber(file.lines)} lines</span>
                      <span>{file.todos} markers</span>
                    </div>
                  ))}
                </div>
              </article>
            </div>
          )}

          {activeTab === "files" && (
            <article className="panel files-panel">
              <div className="panel-heading files-heading">
                <div>
                  <p className="section-label">PROJECT EXPLORER</p>
                  <h3>Files</h3>
                </div>
                <input
                  className="search-input"
                  type="search"
                  placeholder="Filter by path…"
                  value={fileQuery}
                  onChange={(event: ChangeEvent<HTMLInputElement>) => setFileQuery(event.target.value)}
                />
              </div>

              <div className="file-browser">
                {filteredFiles.map((path) => (
                  <div className="browser-row" key={path}>
                    <span className="file-glyph">·</span>
                    <code>{path}</code>
                  </div>
                ))}
              </div>

              {analysis.files_index_truncated && (
                <p className="notice">Explorer is capped at the first 2,000 files for responsive local browsing.</p>
              )}
            </article>
          )}

          {activeTab === "todos" && (
            <article className="panel">
              <div className="panel-heading">
                <div>
                  <p className="section-label">TODO / FIXME / HACK / XXX</p>
                  <h3>Maintenance markers</h3>
                </div>
                <span className="muted">up to 500 results</span>
              </div>

              {analysis.todos.length ? (
                <div className="todo-list">
                  {analysis.todos.map((todo, index) => (
                    <div className="todo-row" key={`${todo.path}-${todo.line}-${index}`}>
                      <span className={`tag tag-${todo.tag.toLowerCase()}`}>{todo.tag}</span>
                      <div>
                        <strong>{todo.text || "No description"}</strong>
                        <span>{todo.path}:{todo.line}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="empty-state">No maintenance markers found in recognized source files.</p>
              )}
            </article>
          )}

          {activeTab === "git" && (
            <div className="panel-grid">
              <article className="panel">
                <div className="panel-heading">
                  <div>
                    <p className="section-label">GIT</p>
                    <h3>Repository state</h3>
                  </div>
                </div>

                {analysis.git ? (
                  <div className="git-grid">
                    <div><span>Branch</span><strong>{analysis.git.branch ?? "detached HEAD"}</strong></div>
                    <div><span>Commits</span><strong>{formatNumber(analysis.git.commits)}</strong></div>
                    <div><span>Tracked</span><strong>{formatNumber(analysis.git.tracked_files)}</strong></div>
                    <div><span>Changed</span><strong>{formatNumber(analysis.git.changed_files)}</strong></div>
                  </div>
                ) : (
                  <p className="empty-state">This folder is not inside a readable Git work tree.</p>
                )}
              </article>

              <article className="panel">
                <div className="panel-heading">
                  <div>
                    <p className="section-label">DEPENDENCIES</p>
                    <h3>Detected manifests</h3>
                  </div>
                </div>

                {analysis.dependency_manifests.length ? (
                  <div className="manifest-list">
                    {analysis.dependency_manifests.map((manifest) => (
                      <div className="manifest-row" key={manifest.path}>
                        <div>
                          <strong>{manifest.path}</strong>
                          <span>{manifest.kind}</span>
                        </div>
                        <strong>{manifest.dependencies ?? "—"}</strong>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="empty-state">No supported dependency manifest found.</p>
                )}
              </article>
            </div>
          )}
        </section>
      )}

      <footer>
        <span>CodeScope runs locally.</span>
        <span>Your source stays on your machine.</span>
      </footer>
    </main>
  );
}

export default App;
