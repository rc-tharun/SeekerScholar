import React, { useState, useRef, useEffect } from 'react'
import './App.css'

interface SearchResult {
  id: number
  title: string
  abstract: string
  link: string
  score: number
  method: string
}

interface FileSearchResponse {
  extracted_query: string
  mode: "bert" | "hybrid"
  results: SearchResult[]
}

interface MethodEvaluation {
  method: string
  teacher_ndcg_at_10: number
  teacher_precision_at_10: number
  teacher_top1_score: number
  num_results: number
}

interface SearchWithEvaluationResponse {
  results: SearchResult[]
  method: string
  evaluations: MethodEvaluation[]
}

interface FileSearchWithEvaluationResponse {
  extracted_query: string
  results: SearchResult[]
  method: string
  evaluations: MethodEvaluation[]
}

// API base URL: use VITE_API_BASE_URL if set, otherwise fallback to VITE_API_URL, then localhost
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [query, setQuery] = useState('')
  const [method, setMethod] = useState('hybrid')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [extractedQuery, setExtractedQuery] = useState<string | null>(null)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [evaluations, setEvaluations] = useState<MethodEvaluation[]>([])
  const [teacherModelName, setTeacherModelName] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const isCancelledRef = useRef<boolean>(false)

  // Fetch teacher model name on component mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/config/teacher-model`)
      .then(res => res.json())
      .then(data => setTeacherModelName(data.teacher_model_name))
      .catch(err => console.error('Failed to fetch teacher model name:', err))
  }, [])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    // Cancel previous in-flight request (if any)
    if (abortRef.current) {
      console.log('Cancelling previous request before starting new one')
      abortRef.current.abort()
      abortRef.current = null
    }

    // Reset cancellation flag
    isCancelledRef.current = false
    console.log('Starting new search, query:', query.trim())

    // Create new AbortController for this request
    const controller = new AbortController()
    abortRef.current = controller

    setLoading(true)
    setError(null)
    setResults([])
    setExtractedQuery(null)
    setEvaluations([])

    try {
      // Use the new endpoint that includes evaluation
      const response = await fetch(`${API_BASE_URL}/search-with-evaluation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          method: method,
          top_k: 10,
        }),
        signal: controller.signal,
      })

      // Check if cancelled before processing
      if (isCancelledRef.current || controller.signal.aborted) {
        return
      }

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Search failed')
      }

      const data: SearchWithEvaluationResponse = await response.json()
      
      // Only update state if not cancelled and controller is still current
      if (!isCancelledRef.current && abortRef.current === controller && !controller.signal.aborted) {
        setResults(data.results)
        setEvaluations(data.evaluations)
      }
    } catch (err: any) {
      // Handle abort gracefully - don't show error if user cancelled
      if (err.name === 'AbortError' || controller.signal.aborted || isCancelledRef.current) {
        console.log('Search aborted by user')
        return // Exit early, don't update any state
      } else {
        // Only set error if not cancelled and controller is still current
        if (!isCancelledRef.current && abortRef.current === controller) {
          setError(err instanceof Error ? err.message : 'An error occurred')
        }
      }
    } finally {
      // Always clear loading if this is still the current request OR if it was cancelled
      const shouldClear = abortRef.current === controller || isCancelledRef.current
      if (shouldClear) {
        setLoading(false)
        if (abortRef.current === controller) {
          abortRef.current = null
        }
        // Reset cancellation flag only if this was the cancelled request
        if (isCancelledRef.current && abortRef.current === null) {
          isCancelledRef.current = false
        }
      }
    }
  }

  const handleCancelSearch = () => {
    console.log('Cancel button clicked, abortRef.current:', abortRef.current, 'loading:', loading)
    
    if (abortRef.current) {
      const controller = abortRef.current
      
      // Mark as cancelled FIRST - this prevents any state updates
      isCancelledRef.current = true
      
      // Abort the HTTP request
      controller.abort()
      console.log('Request aborted, signal.aborted:', controller.signal.aborted)
      
      // Immediately clear loading state - force UI update
      setLoading(false)
      setError(null)
      
      // Clear results to prevent stale data from cancelled request
      setResults([])
      setEvaluations([])
      setExtractedQuery(null)
      
      // Clear the ref AFTER setting loading to false
      abortRef.current = null
      
      console.log('Cancel complete - loading should be false now')
    } else {
      // Even if no controller, clear loading state (safety fallback)
      console.log('No active request to cancel, but clearing loading state')
      setLoading(false)
      setError(null)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    const ext = file.name.toLowerCase().split('.').pop()
    const supportedTypes = ['pdf', 'docx', 'doc', 'txt']
    if (!ext || !supportedTypes.includes(ext)) {
      setError('Please upload a supported file type (PDF, DOCX, or TXT)')
      return
    }

    // Cancel previous in-flight request (if any)
    if (abortRef.current) {
      abortRef.current.abort()
      console.log('Previous request aborted by new file upload.')
    }

    // Create new AbortController for this request
    const controller = new AbortController()
    abortRef.current = controller
    isCancelledRef.current = false // Reset cancellation flag for new request

    setUploadedFile(file)
    setLoading(true)
    setError(null)
    setResults([])
    setExtractedQuery(null)
    setEvaluations([]) // Clear evaluations for new file upload
    setQuery('') // Clear text query

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('method', method) // Use the selected method from dropdown
      formData.append('top_k', '10')

      const response = await fetch(`${API_BASE_URL}/search-file-with-evaluation`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })

      // Check if request was aborted before processing response
      if (controller.signal.aborted || isCancelledRef.current) {
        console.log('File search response received after cancellation, ignoring.')
        return
      }

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'File search failed')
      }

      const data: FileSearchWithEvaluationResponse = await response.json()
      
      // Only update state if this controller is still the current one and not aborted
      if (abortRef.current === controller && !controller.signal.aborted && !isCancelledRef.current) {
        setExtractedQuery(data.extracted_query)
        setResults(data.results)
        setEvaluations(data.evaluations) // Set evaluations from file search
      }
    } catch (err: any) {
      // Handle abort gracefully - don't show error if user cancelled
      if (err.name === 'AbortError' || controller.signal.aborted || isCancelledRef.current) {
        console.log('File search aborted by user or new file upload started.')
        return // Exit early, don't update any state
      } else {
        // Only set error if this controller is still the current one and not explicitly cancelled
        if (abortRef.current === controller) {
          setError(err instanceof Error ? err.message : 'An error occurred')
        }
      }
    } finally {
      // Always clear loading if this is still the current request or if it was explicitly cancelled
      if (abortRef.current === controller || isCancelledRef.current) {
        setLoading(false)
        if (abortRef.current === controller) {
          abortRef.current = null // Clear the ref only if it's still pointing to this controller
        }
        isCancelledRef.current = false // Reset cancellation flag
      }
      setUploadedFile(null)
      // Reset file input
      e.target.value = ''
    }
  }

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>🔬 SeekerScholar</h1>
          <p className="subtitle">Your research buddy - Search academic papers using BM25, BERT, PageRank, or Hybrid methods</p>
        </header>

        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-group">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your search query..."
              className="search-input"
              disabled={loading}
            />
            {loading ? (
              <button 
                type="button" 
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  handleCancelSearch()
                }}
                className="cancel-button"
              >
                Cancel Search
              </button>
            ) : (
              <button type="submit" className="search-button" disabled={loading}>
                Search
              </button>
            )}
          </div>

          <div className="method-selector">
            <label>Search Method:</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="method-select"
              disabled={loading}
            >
              <option value="hybrid">Hybrid (Recommended)</option>
              <option value="bm25">BM25 (Keyword)</option>
              <option value="bert">BERT (Semantic)</option>
              <option value="pagerank">PageRank (Authority)</option>
            </select>
          </div>
        </form>

        <div className="file-upload-section">
          <div className="file-upload-divider">
            <span>OR</span>
          </div>
          <div className="file-upload-container">
            <label htmlFor="file-upload" className="file-upload-label">
              📄 Upload file (PDF, DOCX, TXT) to find similar papers
            </label>
            <input
              id="file-upload"
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              onChange={handleFileUpload}
              className="file-upload-input"
              disabled={loading}
            />
            {uploadedFile && (
              <div className="file-name">
                Selected: {uploadedFile.name}
              </div>
            )}
          </div>
        </div>

        {extractedQuery && (
          <div className="extracted-query">
            <h3>Extracted Query:</h3>
            <div className="extracted-query-text">
              {extractedQuery.length > 500
                ? `${extractedQuery.substring(0, 500)}...`
                : extractedQuery}
            </div>
          </div>
        )}

        {evaluations.length > 0 && (
          <div className="metrics-panel">
            <h3>
              📊 Method Comparison
              {teacherModelName && (
                <span className="teacher-model-name" title={`Cross-Encoder judge model used for evaluation: ${teacherModelName}`}>
                  {' '}(Cross-Encoder Judge: {teacherModelName})
                </span>
              )}
            </h3>
            {(() => {
              const bestModel = evaluations.reduce((best, current) => 
                current.teacher_ndcg_at_10 > best.teacher_ndcg_at_10 ? current : best
              )
              return (
                <p className="metrics-summary">
                  <strong>
                    Best model for this query (NDCG@10 with {teacherModelName || 'Cross-Encoder'}): {bestModel.method.toUpperCase()}
                  </strong>
                  {' '}(NDCG@10: {bestModel.teacher_ndcg_at_10.toFixed(3)})
                </p>
              )
            })()}
            <p className="metrics-description">
              Ranking metrics from a pre-trained cross-encoder teacher model. NDCG@10 measures ranking quality, Precision@10 measures relevance, and Top1 is the score of the first result.
            </p>
            <div className="metrics-grid">
              {evaluations.map((evaluation) => {
                const isSelected = evaluation.method === method
                const isBest = evaluation.teacher_ndcg_at_10 === Math.max(...evaluations.map(e => e.teacher_ndcg_at_10))
                return (
                  <div 
                    key={evaluation.method} 
                    className={`metric-card ${isSelected ? 'selected' : ''} ${isBest ? 'best' : ''}`}
                  >
                    <div className="metric-header">
                      <span className="metric-method">{evaluation.method.toUpperCase()}</span>
                      {isSelected && <span className="metric-badge">Selected</span>}
                      {isBest && <span className="metric-badge best-badge">🏆 Best</span>}
                    </div>
                    <div className="metric-scores">
                      <div className="metric-score">
                        <span className="score-label">NDCG@10:</span>
                        <span className="score-value">{evaluation.teacher_ndcg_at_10.toFixed(3)}</span>
                      </div>
                      <div className="metric-score">
                        <span className="score-label">Precision@10:</span>
                        <span className="score-value">{evaluation.teacher_precision_at_10.toFixed(3)}</span>
                      </div>
                      <div className="metric-score">
                        <span className="score-label">Top1 Score:</span>
                        <span className="score-value">{evaluation.teacher_top1_score.toFixed(3)}</span>
                      </div>
                      <div className="metric-score">
                        <span className="score-label">Results:</span>
                        <span className="score-value">{evaluation.num_results}</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Searching papers...</p>
          </div>
        )}

        {results.length > 0 && (
          <div className="results">
            <h2 className="results-header">
              Found {results.length} result{results.length !== 1 ? 's' : ''}
            </h2>
            <div className="results-list">
              {results.map((result, index) => (
                <div key={result.id} className="result-card">
                  <div className="result-header">
                    <span className="result-rank">#{index + 1}</span>
                    <span className="result-method">{result.method.toUpperCase()}</span>
                    <span className="result-score">Score: {result.score.toFixed(4)}</span>
                  </div>
                  <h3 className="result-title">{result.title}</h3>
                  <p className="result-abstract">
                    {result.abstract.length > 300
                      ? `${result.abstract.substring(0, 300)}...`
                      : result.abstract}
                  </p>
                  <a
                    href={result.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="result-link"
                  >
                    View on arXiv →
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {!loading && results.length === 0 && query && !error && (
          <div className="no-results">
            <p>No results found. Try a different query.</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App

