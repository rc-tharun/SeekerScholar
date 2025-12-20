"""
FastAPI application for SeekerScholar paper search engine.
Main API endpoints for text and PDF-based search.

================================================================================
API CONTRACT (DO NOT CHANGE - Frontend depends on this exact structure)
================================================================================

Endpoint: POST /search
  Method: POST
  Request Body (JSON):
    {
      "query": str,           # Search query text
      "method": str,          # One of: "bm25", "bert", "pagerank", "hybrid"
      "top_k": int            # Number of results (1-100)
    }
  Response (JSON):
    {
      "query": str,           # Original query
      "method": str,          # Search method used
      "top_k": int,           # Number of results requested
      "results": [            # List of SearchResult objects
        {
          "id": int,
          "title": str,
          "abstract": str,
          "link": str,
          "score": float,
          "method": str
        },
        ...
      ]
    }

Endpoint: GET /search
  Method: GET
  Query Parameters:
    query: str (required)
    method: str (default: "hybrid")
    top_k: int (default: 10)
  Response: Same as POST /search

Endpoint: POST /search-from-pdf
  Method: POST
  Request Body (multipart/form-data):
    file: UploadFile         # PDF, DOCX, or TXT file
    method: str              # One of: "bm25", "bert", "pagerank", "hybrid"
    top_k: int               # Number of results (1-100)
  Response (JSON):
    {
      "extracted_query": str, # Text extracted from file
      "method": str,          # Search method used
      "top_k": int,           # Number of results requested
      "results": [            # List of SearchResult objects (same structure as /search)
        ...
      ]
    }

Endpoint: GET /health
  Method: GET
  Response (JSON):
    {
      "status": str,          # "ok"
      "message": str          # "API is healthy"
    }

================================================================================
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal
import logging
import os

from app.config import Config
from app.engine import SearchEngine, normalize_and_truncate_query
from app.pdf_utils import extract_text_from_file, first_n_words
from app.data_loader import ensure_data_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI instance
app = FastAPI(title="SeekerScholar API", version="1.0.0")

# Ensure data files exist
data_dir = Config.get_data_dir()
logger.info(f"{'='*60}")
logger.info(f"SeekerScholar Backend Starting")
logger.info(f"{'='*60}")
logger.info(f"Data directory: {data_dir}")
logger.info(f"Absolute path: {os.path.abspath(data_dir)}")

# Check artifact status before attempting to load
from app.data_loader import check_data_files
all_exist, missing_files = check_data_files(data_dir)
if all_exist:
    logger.info("✓ All required artifacts present")
    for filename in ["df.pkl", "bm25.pkl", "embeddings.pt", "graph.pkl"]:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            logger.info(f"  ✓ {filename}: {size_mb:.2f} MB")
else:
    logger.warning(f"⚠ Missing artifacts: {', '.join(missing_files)}")
    logger.info("Attempting to download missing artifacts...")

ensure_data_files(data_dir)

# Verify again after download attempt
all_exist, still_missing = check_data_files(data_dir)
if not all_exist:
    logger.error(f"✗ ERROR: Required artifacts still missing: {', '.join(still_missing)}")
    logger.error("Server will start but search functionality may not work.")
else:
    logger.info("✓ All artifacts verified")

# Initialize search engine
logger.info("Initializing search engine...")
try:
    engine = SearchEngine(data_dir=data_dir, cache_size=Config.CACHE_SIZE)
    logger.info("✓ Search engine initialized successfully")
except Exception as e:
    logger.error(f"✗ ERROR: Failed to initialize search engine: {e}")
    logger.error("Server will start but search endpoints will fail.")
    raise

# Add CORS middleware
# Allow origins from environment variable or default to all (for development)
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*":
    allow_origins = ["*"]
else:
    # Split comma-separated origins
    allow_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models (API Contract - DO NOT CHANGE)
class SearchRequest(BaseModel):
    query: str
    method: Literal["bm25", "bert", "pagerank", "hybrid"] = "hybrid"
    top_k: int = 10


class SearchResult(BaseModel):
    id: int
    title: str
    abstract: str
    link: str
    score: float
    method: str


class SearchResponse(BaseModel):
    query: str
    method: str
    top_k: int
    results: List[SearchResult]


class HealthResponse(BaseModel):
    status: str
    message: str
    artifacts: dict[str, bool]
    data_dir: str


class PdfSearchResponse(BaseModel):
    extracted_query: str
    method: str
    top_k: int
    results: List[SearchResult]


# Endpoints
@app.get("/", response_model=HealthResponse)
def root():
    """Root endpoint."""
    return {"status": "ok", "message": "SeekerScholar API"}


@app.get("/health", response_model=HealthResponse)
def health():
    """
    Health check endpoint.
    Returns API status and artifact availability (without exposing file contents).
    """
    from app.data_loader import check_data_files
    
    data_dir = Config.get_data_dir()
    all_exist, missing_files = check_data_files(data_dir)
    
    # Check individual artifacts
    artifacts = {
        "bm25": os.path.exists(Config.artifact_path("bm25.pkl")),
        "df": os.path.exists(Config.artifact_path("df.pkl")),
        "graph": os.path.exists(Config.artifact_path("graph.pkl")),
        "embeddings": os.path.exists(Config.artifact_path("embeddings.pt")),
    }
    
    if all_exist:
        return {
            "status": "ok",
            "message": "API is healthy",
            "artifacts": artifacts,
            "data_dir": data_dir
        }
    else:
        return {
            "status": "degraded",
            "message": "API is running but some artifacts are missing",
            "artifacts": artifacts,
            "data_dir": data_dir
        }


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """
    Search for papers using the specified method.
    
    - method="bm25": Keyword-based search
    - method="bert": Semantic search using BERT embeddings
    - method="pagerank": Authority-based search using citation graph
    - method="hybrid": Combined approach (default)
    """
    # Validate request
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")
    
    try:
        Config.validate_top_k(request.top_k)
        Config.validate_method(request.method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        # Preprocess and normalize query (handles truncation internally)
        query = normalize_and_truncate_query(request.query)
        
        # Execute search
        if request.method == "bm25":
            results = engine.search_bm25(query, top_k=request.top_k)
        elif request.method == "bert":
            results = engine.search_bert(query, top_k=request.top_k)
        elif request.method == "pagerank":
            results = engine.search_pagerank(query, top_k=request.top_k)
        elif request.method == "hybrid":
            results = engine.search_hybrid(query, top_k=request.top_k)
        
        # Format response
        response = SearchResponse(
            query=query,
            method=request.method,
            top_k=request.top_k,
            results=results
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/search", response_model=SearchResponse)
def search_get(query: str, top_k: int = 10, method: str = "hybrid"):
    """
    GET endpoint for search (convenience).
    """
    request = SearchRequest(query=query, top_k=top_k, method=method)
    return search(request)


@app.post("/search-from-pdf", response_model=PdfSearchResponse)
async def search_from_pdf(
    file: UploadFile = File(...),
    method: str = "hybrid",
    top_k: int = 10
):
    """
    Upload a file (PDF, DOCX, or TXT), extract text, and search for similar papers.
    
    - method="bm25": Keyword-based search
    - method="bert": Semantic search using BERT embeddings
    - method="pagerank": Authority-based search using citation graph
    - method="hybrid": Combined approach (default)
    
    Supported file types: PDF, DOCX, TXT
    """
    # Validate parameters
    try:
        Config.validate_top_k(top_k)
        Config.validate_method(method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    
    ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    supported_extensions = ["pdf", "docx", "doc", "txt"]
    if ext not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Supported types: PDF, DOCX, TXT"
        )
    
    try:
        # Extract text from file
        file_content = await file.read()
        raw_extracted_text = await extract_text_from_file(
            file_content=file_content,
            filename=file.filename,
            max_length=Config.MAX_QUERY_LENGTH
        )
        
        if not raw_extracted_text or not raw_extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from file. Please ensure the file contains readable text."
            )
        
        # Normalize extracted text (for display in response)
        extracted_text = normalize_and_truncate_query(raw_extracted_text)
        
        # For file uploads: use only first 100 words as search query
        # This speeds up search while keeping the full extracted text in the response
        search_query = first_n_words(extracted_text, n=100)
        search_query = normalize_and_truncate_query(search_query)
        
        # Run search using first 100 words only
        if method == "bm25":
            results = engine.search_bm25(search_query, top_k=top_k)
        elif method == "bert":
            results = engine.search_bert(search_query, top_k=top_k)
        elif method == "pagerank":
            results = engine.search_pagerank(search_query, top_k=top_k)
        elif method == "hybrid":
            results = engine.search_hybrid(search_query, top_k=top_k)
        
        # Format response (return full extracted_query, not the 100-word query)
        response = PdfSearchResponse(
            extracted_query=extracted_text,  # Full extracted text for display
            method=method,
            top_k=top_k,
            results=results
        )
        
        return response
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"File search error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
