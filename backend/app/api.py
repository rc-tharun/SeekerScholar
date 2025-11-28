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
# Data directory can be configured via DATA_DIR environment variable
# Defaults to ../data relative to backend root for local development
# For Render, use absolute path or relative to app directory
data_dir = os.getenv("DATA_DIR", "../data")

# If data files don't exist, try to download them (for Render deployment)
data_file_path = os.path.join(data_dir, "df.pkl")
if not os.path.exists(data_file_path):
    print("Data files not found. Attempting to download...")
    try:
        # Try to run download script from backend root
        import subprocess
        # Get the backend root directory (parent of app/)
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(backend_root, "download_data.py")
        
        # Also try current directory and common locations
        possible_paths = [
            script_path,
            os.path.join(os.path.dirname(__file__), "..", "download_data.py"),
            "download_data.py",
            os.path.join(os.getcwd(), "download_data.py"),
        ]
        
        script_found = False
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                print(f"Found download script at: {abs_path}")
                result = subprocess.run([sys.executable, abs_path], check=False, capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print(f"Download script stderr: {result.stderr}")
                script_found = True
                break
        
        if not script_found:
            print(f"Warning: download_data.py not found. Tried: {possible_paths}")
            print("Please ensure data files are downloaded during build or set DATA_DIR correctly.")
    except Exception as e:
        print(f"Warning: Could not download data files: {e}")
        import traceback
        traceback.print_exc()
        print("Please ensure data files are available or set DATA_DIR correctly.")

# Check again if files exist after download attempt
if not os.path.exists(data_file_path):
    print(f"ERROR: Data file still not found at: {os.path.abspath(data_file_path)}")
    print(f"Data directory: {os.path.abspath(data_dir)}")
    print("Please check:")
    print("1. Build command includes: python download_data.py")
    print("2. DATA_DIR environment variable is set correctly")
    print("3. Google Drive files are accessible")
    raise FileNotFoundError(f"Data file not found: {data_file_path}")

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

