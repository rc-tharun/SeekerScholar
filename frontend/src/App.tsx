import React, { useState, useRef } from 'react'
import './App.css'
import { apiPost, apiPostFormData } from './lib/api'

interface SearchResult {
  id: number
  title: string
  abstract: string
  link: string
  score: number
  method: string
}

interface SearchResponse {
  query: string
  method: string
  top_k: number
  results: SearchResult[]
}

interface PdfSearchResponse {
  extracted_query: string
  method: string
  top_k: number
  results: SearchResult[]
}

function App() {
  const [query, setQuery] = useState('')
  const [method, setMethod] = useState('hybrid')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [extractedQuery, setExtractedQuery] = useState<string | null>(null)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const isCancelledRef = useRef<boolean>(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    // Cancel previous in-flight request (if any)
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }

    // Reset cancellation flag
    isCancelledRef.current = false

    // Create new AbortController for this request
    const controller = new AbortController()
    abortRef.current = controller

    setLoading(true)
    setError(null)
    setResults([])
    setExtractedQuery(null)

    try {
      const data: SearchResponse = await apiPost<SearchResponse>(
        '/search',
        {
          query: query.trim(),
          method: method,
          top_k: 10,
        },
        controller.signal
      )

      // Check if cancelled before processing
      if (isCancelledRef.current || controller.signal.aborted) {
        return
      }
      
      // Only update state if not cancelled and controller is still current
      if (!isCancelledRef.current && abortRef.current === controller && !controller.signal.aborted) {
        setResults(data.results)
      }
    } catch (err: any) {
      // Handle abort gracefully - don't show error if user cancelled
      if (err.name === 'AbortError' || controller.signal.aborted || isCancelledRef.current) {
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
    
    if (abortRef.current) {
      const controller = abortRef.current
      
      // Mark as cancelled FIRST - this prevents any state updates
      isCancelledRef.current = true
      
      // Abort the HTTP request
      controller.abort()
      
      // Immediately clear loading state - force UI update
      setLoading(false)
      setError(null)
      
      // Clear results to prevent stale data from cancelled request
      setResults([])
      setExtractedQuery(null)
      
      // Clear the ref AFTER setting loading to false
      abortRef.current = null
    } else {
      // Even if no controller, clear loading state (safety fallback)
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
    setQuery('') // Clear text query

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('method', method)
      formData.append('top_k', '10')

      // Check if request was aborted before processing response
      if (controller.signal.aborted || isCancelledRef.current) {
        return
      }

      const data: PdfSearchResponse = await apiPostFormData<PdfSearchResponse>(
        '/search-from-pdf',
        formData,
        controller.signal
      )
      
      // Only update state if this controller is still the current one and not aborted
      if (abortRef.current === controller && !controller.signal.aborted && !isCancelledRef.current) {
        setExtractedQuery(data.extracted_query)
        setResults(data.results)
      }
    } catch (err: any) {
      // Handle abort gracefully - don't show error if user cancelled
      if (err.name === 'AbortError' || controller.signal.aborted || isCancelledRef.current) {
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
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="method-select"
              disabled={loading}
            >
              <option value="bm25">BM25</option>
              <option value="bert">BERT</option>
              <option value="pagerank">PageRank</option>
              <option value="hybrid">Hybrid</option>
            </select>
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
        </form>

        <div className="file-upload-section">
          <div className="file-upload-divider">
            <span>OR</span>
          </div>
          <div className="file-upload-container">
            <label htmlFor="file-upload" className="file-upload-label">
              📄 Upload file (PDF, DOCX, TXT) to find similar papers
            </label>
            <div className="file-upload-with-method">
              <input
                id="file-upload"
                type="file"
                accept=".pdf,.docx,.doc,.txt"
                onChange={handleFileUpload}
                className="file-upload-input"
                disabled={loading}
              />
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                className="method-select"
                disabled={loading}
              >
                <option value="bm25">BM25</option>
                <option value="bert">BERT</option>
                <option value="pagerank">PageRank</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </div>
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
