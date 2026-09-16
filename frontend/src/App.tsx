import { useState, type FormEvent } from "react";
import "./App.css";

type FileAnalysis = {
  path: string;
  lines: number;
  language: string;
};

type RepositoryAnalysis = {
  name: string;
  files: number;
  lines: number;
  languages: Record<string, number>;
  largest_files: FileAnalysis[];
};

function App() {
  const [repositoryPath, setRepositoryPath] = useState("");
  const [analysis, setAnalysis] = useState<RepositoryAnalysis | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleAnalyze(event: FormEvent) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setAnalysis(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/analyze",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            path: repositoryPath,
          }),
        }
      );

      if (!response.ok) {
        const data = await response.json();

        throw new Error(
          data.detail ?? "Unable to analyze repository."
        );
      }

      const data: RepositoryAnalysis = await response.json();

      setAnalysis(data);
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("Something went wrong.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app">
      <section className="hero">
        <p className="eyebrow">CODESCOPE</p>

        <h1>Understand your codebase.</h1>

        <p className="description">
          Analyze a local repository and get a clear overview
          of its structure.
        </p>

        <form onSubmit={handleAnalyze}>
          <input
            type="text"
            placeholder="C:\Users\Franklys\CodeScope"
            value={repositoryPath}
            onChange={(event) =>
              setRepositoryPath(event.target.value)
            }
          />

          <button
            type="submit"
            disabled={loading || !repositoryPath.trim()}
          >
            {loading ? "Analyzing..." : "Analyze repository"}
          </button>
        </form>

        {error && <p className="error">{error}</p>}
      </section>

      {analysis && (
        <section className="results">
          <div className="repository-heading">
            <span>Repository</span>
            <h2>{analysis.name}</h2>
          </div>

          <div className="stats">
            <article>
              <span>Files</span>
              <strong>{analysis.files}</strong>
            </article>

            <article>
              <span>Lines</span>
              <strong>{analysis.lines}</strong>
            </article>

            <article>
              <span>Languages</span>
              <strong>
                {Object.keys(analysis.languages).length}
              </strong>
            </article>
          </div>

          <div className="languages">
            <h3>Languages</h3>

            {Object.entries(analysis.languages).map(
              ([language, files]) => (
                <div
                  className="language"
                  key={language}
                >
                  <span>{language}</span>
                  <strong>{files} files</strong>
                </div>
              )
            )}
          </div>

          <div className="largest-files">
            <h3>Largest files</h3>

            {analysis.largest_files.map((file) => (
              <div className="file-row" key={file.path}>
                <div>
                  <strong>{file.path}</strong>
                  <span>{file.language}</span>
                </div>

                <strong>{file.lines} lines</strong>
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

export default App;