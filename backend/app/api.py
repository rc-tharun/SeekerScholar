"""
FastAPI application for paper search engine.
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal, Tuple
import os
import sys
import re
import tempfile
from pypdf import PdfReader
from docx import Document

from app.engine import PaperSearchEngine
from app.teacher import TeacherEvaluator
from app.teacher_metrics import compute_teacher_ndcg_at_k, compute_teacher_precision_at_k, get_teacher_top1_score

# Create FastAPI instance
app = FastAPI(title="SeekerScholar API", version="1.0.0")

# Initialize engine on module import
# Data directory path resolution for Render deployment

def get_data_dir():
    """Get the data directory path, resolving relative paths correctly."""
    # Get the backend root (where download_data.py is)
    # api.py is at: /app/app/api.py (when root directory is 'backend')
    # So backend root is: /app/
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check if DATA_DIR is set
    data_dir_env = os.getenv("DATA_DIR")
    
    if data_dir_env:
        # If absolute path, use it
        if os.path.isabs(data_dir_env):
            return data_dir_env
        # If relative, resolve from backend root
        resolved = os.path.join(backend_root, data_dir_env)
        return os.path.normpath(os.path.abspath(resolved))
    else:
        # Default: ../data relative to backend root
        # backend_root = /app/ (backend directory)
        # In Render with root directory 'backend':
        # - /app/ = backend/ directory
        # - /app/../ = repo root (parent of backend)
        # - /app/../data = repo root / data
        
        # First try: ../data from backend root
        data_dir_candidate = os.path.join(backend_root, "..", "data")
        data_dir_candidate = os.path.normpath(os.path.abspath(data_dir_candidate))
        
        # Check if this resolves to /data (which would be wrong - system root)
        # If so, use ./data in backend root instead
        if data_dir_candidate == "/data" or not os.path.exists(os.path.dirname(data_dir_candidate)):
            # Fallback: use ./data in backend root
            data_dir = os.path.join(backend_root, "data")
            print(f"Using data directory in backend root: {data_dir}")
        else:
            data_dir = data_dir_candidate
            print(f"Using data directory from repo root: {data_dir}")
        
        return data_dir

def download_data_files(data_dir):
    """Download data files if they don't exist - inline download without script."""
    print(f"Downloading data files directly to: {data_dir}")
    
    # Ensure directory exists
    os.makedirs(data_dir, exist_ok=True)
    
    try:
        # Import gdown directly
        try:
            import gdown
        except ImportError:
            print("Installing gdown...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"], 
                                capture_output=True)
            import gdown
        
        # Google Drive file IDs
        gdrive_files = {
            "df.pkl": "1DzBhRncYzif5bsbgIDxxgxb05T9mh8-h",
            "bm25.pkl": "1LZBDvDHKCylR2YRzUrywvDaREVXpEc4Y",
            "embeddings.pt": "12e382jL02z56gz5fPOINxBxHYVTBqIBb",
            "graph.pkl": "1KX1Bl54xINL75QOhtA9Av_9SBJxVuYPU",
        }
        
        downloaded = []
        failed = []
        
        for filename, file_id in gdrive_files.items():
            output_path = os.path.join(data_dir, filename)
            url = f"https://drive.google.com/uc?id={file_id}"
            
            try:
                print(f"Downloading {filename}...")
                gdown.download(url, output_path, quiet=False)
                
                if os.path.exists(output_path):
                    size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    print(f"✓ {filename}: {size_mb:.2f} MB")
                    downloaded.append(filename)
                else:
                    print(f"✗ {filename}: Download completed but file not found")
                    failed.append(filename)
            except Exception as e:
                print(f"✗ {filename}: Error - {e}")
                failed.append(filename)
        
        if failed:
            print(f"\nFailed to download: {', '.join(failed)}")
            return False
        
        print(f"\n✓ Successfully downloaded all {len(downloaded)} files!")
        return True
        
    except Exception as e:
        print(f"ERROR during download: {e}")
        import traceback
        traceback.print_exc()
        return False

# Get data directory
data_dir = get_data_dir()
# Ensure it's an absolute path
if not os.path.isabs(data_dir):
    data_dir = os.path.abspath(data_dir)

print(f"\n{'='*60}")
print(f"DATA DIRECTORY CONFIGURATION")
print(f"{'='*60}")
print(f"Data directory: {data_dir}")
print(f"Absolute path: {os.path.abspath(data_dir)}")
print(f"Directory exists: {os.path.exists(data_dir)}")
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"Backend root: {backend_root}")
print(f"Current working directory: {os.getcwd()}")
print(f"Expected data path from backend root: {os.path.abspath(os.path.join(backend_root, '..', 'data'))}")
print(f"{'='*60}\n")

# Check if data files exist
required_files = ["df.pkl", "bm25.pkl", "embeddings.pt", "graph.pkl"]
missing_files = []

for filename in required_files:
    filepath = os.path.join(data_dir, filename)
    if not os.path.exists(filepath):
        missing_files.append(filename)
        print(f"✗ Missing: {filename} at {filepath}")

# If any files are missing, try to download them
if missing_files:
    print(f"\n{'='*60}")
    print(f"DOWNLOADING MISSING FILES: {', '.join(missing_files)}")
    print(f"{'='*60}\n")
    
    success = download_data_files(data_dir)
    
    if not success:
        print("\nERROR: Download script failed!")
    
    # Check again
    still_missing = []
    for filename in missing_files:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"✓ {filename}: {size_mb:.2f} MB")
        else:
            still_missing.append(filename)
            print(f"✗ {filename}: STILL MISSING")

    if still_missing:
        print(f"\n{'='*60}")
        print(f"ERROR: Could not download files: {', '.join(still_missing)}")
        print(f"{'='*60}")
        print(f"Data directory: {data_dir}")
        if os.path.exists(data_dir):
            print(f"Directory contents: {os.listdir(data_dir)}")
        else:
            print("Data directory does not exist!")
        print(f"\nTroubleshooting:")
        print(f"1. Check build logs for download errors")
        print(f"2. Verify Google Drive files are accessible")
        print(f"3. Check DATA_DIR environment variable")
        print(f"4. Verify network connectivity in Render")
        raise FileNotFoundError(f"Data files not found: {', '.join(still_missing)}")
else:
    print("✓ All data files found!")

print(f"\n{'='*60}")
print(f"INITIALIZING ENGINE")
print(f"{'='*60}\n")
engine = PaperSearchEngine(data_dir=data_dir)

# Initialize teacher evaluator
teacher = TeacherEvaluator()

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    method: str = "hybrid"  # "bm25", "bert", "pagerank", or "hybrid"


class SearchResult(BaseModel):
    id: int
    title: str
    abstract: str
    link: str
    score: float
    method: str


class HealthResponse(BaseModel):
    status: str
    message: str


class TeacherModelResponse(BaseModel):
    teacher_model_name: str


class FileSearchResponse(BaseModel):
    extracted_query: str
    mode: Literal["bert", "hybrid"]
    results: List[SearchResult]


class MethodEvaluation(BaseModel):
    method: str
    teacher_ndcg_at_10: float
    teacher_precision_at_10: float
    teacher_top1_score: float
    num_results: int


class SearchWithEvaluationResponse(BaseModel):
    results: List[SearchResult]
    method: str
    evaluations: List[MethodEvaluation]


class FileSearchWithEvaluationResponse(BaseModel):
    extracted_query: str
    results: List[SearchResult]
    method: str
    evaluations: List[MethodEvaluation]


# Endpoints
@app.get("/", response_model=HealthResponse)
def root():
    """Root endpoint."""
    return {"status": "ok", "message": "SeekerScholar API"}


@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint."""
    return {"status": "ok", "message": "API is healthy"}


@app.get("/config/teacher-model", response_model=TeacherModelResponse)
def get_teacher_model():
    """
    Get the name of the Cross-Encoder judge model used for method evaluation.
    """
    return {"teacher_model_name": teacher.model_name}


@app.post("/search", response_model=List[SearchResult])
def search(request: SearchRequest):
    """
    Search for papers using the specified method.
    
    - method="bm25": Keyword-based search
    - method="bert": Semantic search using BERT embeddings
    - method="pagerank": Authority-based search using citation graph
    - method="hybrid": Combined approach (default)
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")
    
    if request.top_k < 1 or request.top_k > 100:
        raise HTTPException(
            status_code=400, 
            detail="top_k must be between 1 and 100."
        )
    
    try:
        if request.method == "bm25":
            results = engine.search_bm25(request.query, top_k=request.top_k)
        elif request.method == "bert":
            results = engine.search_bert(request.query, top_k=request.top_k)
        elif request.method == "pagerank":
            results = engine.search_pagerank(request.query, top_k=request.top_k)
        elif request.method == "hybrid":
            results = engine.search_hybrid(request.query, top_k=request.top_k)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid method: {request.method}. Must be one of: bm25, bert, pagerank, hybrid"
            )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/search", response_model=List[SearchResult])
def search_get(query: str, top_k: int = 10, method: str = "hybrid"):
    """
    GET endpoint for search (convenience).
    """
    request = SearchRequest(query=query, top_k=top_k, method=method)
    return search(request)


def evaluate_all_methods(query: str, top_k: int, selected_method: str = "hybrid") -> Tuple[List[SearchResult], List[MethodEvaluation]]:
    """
    Shared helper function to evaluate all search methods for a given query.
    Returns results for the selected method and evaluations for all methods.
    
    Args:
        query: Search query string
        top_k: Number of results to return
        selected_method: Method to use for results (default: "hybrid")
        
    Returns:
        Tuple of (results for selected method, list of evaluations for all methods)
    """
    # Get results for the selected method
    if selected_method == "bm25":
        results = engine.search_bm25(query, top_k=top_k)
    elif selected_method == "bert":
        results = engine.search_bert(query, top_k=top_k)
    elif selected_method == "pagerank":
        results = engine.search_pagerank(query, top_k=top_k)
    elif selected_method == "hybrid":
        results = engine.search_hybrid(query, top_k=top_k)
    else:
        raise ValueError(f"Invalid method: {selected_method}. Must be one of: bm25, bert, pagerank, hybrid")
    
    # Evaluate all methods
    methods = ["bm25", "bert", "pagerank", "hybrid"]
    evaluations = []
    
    for method in methods:
        # Get results for this method
        if method == "bm25":
            method_results = engine.search_bm25(query, top_k=top_k)
        elif method == "bert":
            method_results = engine.search_bert(query, top_k=top_k)
        elif method == "pagerank":
            method_results = engine.search_pagerank(query, top_k=top_k)
        else:  # hybrid
            method_results = engine.search_hybrid(query, top_k=top_k)
        
        # Prepare document texts for teacher scoring
        docs = []
        for result in method_results:
            title = result.get("title", "")
            abstract = result.get("abstract", "")
            doc_text = f"{title} {abstract}".strip()
            docs.append(doc_text)
        
        # Get teacher scores for all results
        teacher_scores = teacher.score_pairs(query, docs)
        
        # Compute ranking metrics
        k = min(10, len(teacher_scores))
        ndcg10 = compute_teacher_ndcg_at_k(teacher_scores, k=10)
        prec10 = compute_teacher_precision_at_k(teacher_scores, k=10, threshold=0.0)
        top1 = get_teacher_top1_score(teacher_scores)
        
        evaluations.append(MethodEvaluation(
            method=method,
            teacher_ndcg_at_10=ndcg10,
            teacher_precision_at_10=prec10,
            teacher_top1_score=top1,
            num_results=len(method_results)
        ))
    
    return results, evaluations


@app.post("/search-with-evaluation", response_model=SearchWithEvaluationResponse)
def search_with_evaluation(request: SearchRequest):
    """
    Search for papers and evaluate all methods using a teacher model.
    Returns results for the selected method plus evaluation metrics for all methods.
    
    - method="bm25": Keyword-based search
    - method="bert": Semantic search using BERT embeddings
    - method="pagerank": Authority-based search using citation graph
    - method="hybrid": Combined approach (default)
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty.")
    
    if request.top_k < 1 or request.top_k > 100:
        raise HTTPException(
            status_code=400, 
            detail="top_k must be between 1 and 100."
        )
    
    try:
        results, evaluations = evaluate_all_methods(request.query, request.top_k, request.method)
        
        return SearchWithEvaluationResponse(
            results=results,
            method=request.method,
            evaluations=evaluations
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


async def extract_text_from_file(uploaded_file: UploadFile) -> str:
    """
    Extract text from various file types (PDF, DOCX, TXT).
    For PDFs, tries to extract abstract if possible, otherwise returns all text.
    """
    # Get file extension
    filename = uploaded_file.filename or "file"
    ext = os.path.splitext(filename)[1].lower()
    
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        content = await uploaded_file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Extract text based on file type
        if ext == ".pdf":
            text_chunks = []
            reader = PdfReader(tmp_path)
            for page in reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_chunks.append(page_text)
                except Exception:
                    continue
            full_text = "\n".join(text_chunks)
            
            # Try to extract abstract section if present
            abstract_patterns = [
                r"(?i)abstract\s*:?\s*(.+?)(?=\n\s*(?:introduction|1\.|keywords|references))",
                r"(?i)abstract\s*:?\s*(.+?)(?=\n\n)",
            ]
            
            for pattern in abstract_patterns:
                match = re.search(pattern, full_text, re.DOTALL)
                if match:
                    abstract_text = match.group(1).strip()
                    if len(abstract_text) > 50:  # Ensure it's substantial
                        return abstract_text
            
            # If no abstract found, return first 2000 characters or full text if shorter
            if len(full_text) > 2000:
                return full_text[:2000]
            return full_text
            
        elif ext in (".docx", ".doc"):
            doc = Document(tmp_path)
            return "\n".join(p.text for p in doc.paragraphs)
            
        elif ext in (".txt", ""):
            with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {ext}. Supported types: PDF, DOCX, TXT")
            
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/search-file", response_model=FileSearchResponse)
async def search_file(
    file: UploadFile = File(...),
    mode: Literal["bert", "hybrid"] = "hybrid",
    top_k: int = 10
):
    """
    Upload a file (PDF, DOCX, or TXT), extract text, and search for similar papers.
    Legacy endpoint - returns results only, no metrics.
    For metrics, use /search-file-with-evaluation instead.
    
    - mode="bert": Semantic search using BERT embeddings
    - mode="hybrid": Combined approach (default)
    
    Supported file types: PDF, DOCX, TXT
    """
    if top_k < 1 or top_k > 100:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 100."
        )
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    
    ext = os.path.splitext(file.filename)[1].lower()
    supported_extensions = [".pdf", ".docx", ".doc", ".txt"]
    if ext not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported types: PDF, DOCX, TXT"
        )
    
    try:
        # Extract text from file
        extracted_text = await extract_text_from_file(file)
        
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from file. Please ensure the file contains readable text."
            )
        
        # Run search based on mode
        if mode == "bert":
            results = engine.search_bert(extracted_text, top_k=top_k)
        elif mode == "hybrid":
            results = engine.search_hybrid(extracted_text, top_k=top_k)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid mode: {mode}. Must be 'bert' or 'hybrid'"
            )
        
        return FileSearchResponse(
            extracted_query=extracted_text,
            mode=mode,
            results=results
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/search-file-with-evaluation", response_model=FileSearchWithEvaluationResponse)
async def search_file_with_evaluation(
    file: UploadFile = File(...),
    method: str = "hybrid",
    top_k: int = 10
):
    """
    Upload a file (PDF, DOCX, or TXT), extract text, and search with full method comparison.
    Returns results for the selected method plus evaluation metrics for all methods.
    Same behavior as /search-with-evaluation but uses extracted file text as query.
    
    - method="bm25": Keyword-based search
    - method="bert": Semantic search using BERT embeddings
    - method="pagerank": Authority-based search using citation graph
    - method="hybrid": Combined approach (default)
    
    Supported file types: PDF, DOCX, TXT
    """
    if top_k < 1 or top_k > 100:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 100."
        )
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    
    ext = os.path.splitext(file.filename)[1].lower()
    supported_extensions = [".pdf", ".docx", ".doc", ".txt"]
    if ext not in supported_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported types: PDF, DOCX, TXT"
        )
    
    # Validate method
    if method not in ["bm25", "bert", "pagerank", "hybrid"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid method: {method}. Must be one of: bm25, bert, pagerank, hybrid"
        )
    
    try:
        # Extract text from file
        extracted_text = await extract_text_from_file(file)
        
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from file. Please ensure the file contains readable text."
            )
        
        # Use the shared evaluation function
        results, evaluations = evaluate_all_methods(extracted_text, top_k, method)
        
        return FileSearchWithEvaluationResponse(
            extracted_query=extracted_text,
            results=results,
            method=method,
            evaluations=evaluations
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

