# SeekerScholar Presentation Script

## Introduction (30 seconds)

"Good [morning/afternoon/evening]. Today I'm excited to present **SeekerScholar** - a production-ready academic paper search engine that helps researchers find relevant papers quickly and efficiently.

As researchers, we all know the struggle of finding the right papers among thousands of publications. Traditional keyword search often misses semantically similar papers, while browsing through citation networks is time-consuming. SeekerScholar solves this by combining multiple search techniques into one powerful, fast, and user-friendly platform."

---

## What is SeekerScholar? (1 minute)

"SeekerScholar is a web-based academic paper search engine built on the ogbn-arxiv dataset, which contains over 160,000 computer science papers from arXiv.

The system offers **four different search methods**:
- **BM25** for fast keyword-based search
- **BERT** for semantic understanding
- **PageRank** for finding authoritative papers
- **Hybrid** which combines all three for the best results

Users can search in two ways:
1. **Text search** - simply type in a query
2. **File upload** - upload a PDF, DOCX, or text file, and the system extracts the content and finds similar papers

The interface is clean and modern, showing results with relevance scores, paper titles, abstracts, and direct links to arXiv."

---

## Technical Architecture (2 minutes)

"Let me walk you through how SeekerScholar works under the hood.

**Frontend:**
- Built with React and TypeScript
- Modern, responsive UI with real-time search
- Handles file uploads and displays results beautifully

**Backend:**
- FastAPI framework for high-performance REST API
- Clean architecture with separate modules for configuration, search engine, PDF processing, and data loading

**The Search Engine:**
The core innovation is our **2-stage retrieval pipeline**:

**Stage 1 - Fast Candidate Generation:**
- Always starts with BM25, which is extremely fast
- Retrieves the top 300 most relevant candidates based on keyword matching
- This narrows down from 160,000 papers to just 300 in milliseconds

**Stage 2 - Intelligent Re-ranking:**
- Only processes those 300 candidates with more sophisticated methods
- For BERT: computes semantic similarity using neural embeddings
- For PageRank: combines keyword relevance with citation authority
- For Hybrid: intelligently combines all three methods

This approach ensures that even complex neural models only process a small subset, keeping everything fast."

---

## Search Methods Explained (2 minutes)

"Let me explain each search method:

**BM25 Search:**
- Uses traditional keyword matching
- Fast and effective for exact term searches
- Best when you know specific terms or phrases
- Typical response time: under 50 milliseconds

**BERT Search:**
- Uses sentence transformers to understand meaning, not just keywords
- Finds papers that are semantically similar even if they use different terminology
- Great for conceptual searches like 'attention mechanisms in deep learning'
- Processes only the 300 BM25 candidates, so it's still fast - typically under 150 milliseconds

**PageRank Search:**
- Combines keyword relevance with citation network analysis
- Finds papers that are both relevant AND influential
- Uses the citation graph to identify authoritative papers
- PageRank scores are precomputed at startup for instant access
- Typical response time: under 60 milliseconds

**Hybrid Search - The Default:**
- This is our recommended method
- Combines all three approaches with weighted scoring:
  - 30% BM25 for keyword relevance
  - 50% BERT for semantic understanding
  - 20% PageRank for authority
- **How we determined these weights:**
  - These weights are based on information retrieval best practices and heuristic tuning
  - BERT gets the highest weight (50%) because semantic understanding is often the most valuable for finding conceptually similar papers
  - BM25 (30%) provides a solid baseline for keyword matching, ensuring exact term matches are still prioritized
  - PageRank (20%) adds authority signals without overwhelming relevance - we want relevant papers first, then boost authoritative ones
  - Scores are normalized to [0,1] range before combining, ensuring fair contribution from each method
  - These weights can be tuned based on evaluation metrics or user feedback
- Typically under 200 milliseconds, but provides the most comprehensive results"

---

## Performance Optimizations (1.5 minutes)

"We've implemented several key optimizations:

**1. Two-Stage Pipeline:**
- Neural models only process 300 candidates, not 160,000 papers
- This makes BERT and Hybrid searches 500 times faster than naive approaches

**2. Precomputed Data:**
- All embeddings, BM25 index, and PageRank scores are precomputed
- Loaded once at startup, not per-request
- This means instant access during searches

**3. Query Optimization:**
- Text queries are truncated to 2048 characters
- PDF uploads use only the first 100 words as the search query
- This ensures consistent performance regardless of input length

**4. Smart Caching:**
- In-memory LRU cache stores 256 recent search results
- Cached queries return in under 10 milliseconds
- Perfect for repeated searches or similar queries

**5. Efficient Model Loading:**
- All models loaded once at startup
- Shared across all requests
- No per-request overhead"

---

## Key Features (1 minute)

"SeekerScholar includes several user-friendly features:

**Multiple Search Methods:**
- Users can choose the method that best fits their needs
- Dropdown selector for easy switching

**File Upload Support:**
- Upload PDFs, DOCX, or text files
- Automatic text extraction
- Finds papers similar to your document

**Relevance Scores:**
- Each result shows a relevance score
- Higher scores mean better matches
- Helps users quickly identify the most relevant papers

**Direct arXiv Links:**
- One-click access to full papers on arXiv
- No need to manually search

**Real-time Search:**
- Instant feedback as you type
- Cancel button for long-running searches
- Loading indicators for better UX"

---

## Demo Walkthrough (2-3 minutes)

"Now let me show you how it works in practice.

**[If doing live demo, walk through these steps:]**

**Demo 1: Text Search with Hybrid Method**
- Type in a query like 'graph neural networks for recommendation systems'
- Select 'Hybrid' method
- Show the results appearing with scores
- Explain that the top result has the highest combined relevance score
- Click on a result to show the arXiv link

**Demo 2: BERT Semantic Search**
- Switch to BERT method
- Search for 'attention mechanisms'
- Show how it finds papers even if they don't use the exact term 'attention'
- Explain the semantic understanding

**Demo 3: File Upload**
- Upload a sample PDF or text file
- Show the extracted text
- Show the similar papers found
- Explain that it uses the first 100 words for speed

**Demo 4: Different Methods Comparison**
- Same query with different methods
- Show how results differ
- Explain when to use each method"

---

## Technical Stack (30 seconds)

"From a technical perspective:

**Backend:**
- Python 3.11+ with FastAPI
- SentenceTransformers for BERT embeddings
- NetworkX for graph analysis
- PyPDF and python-docx for file processing

**Frontend:**
- React with TypeScript
- Vite for fast development and building
- Modern CSS for responsive design

**Deployment:**
- Backend ready for Render or similar platforms
- Frontend ready for Vercel or Netlify
- Docker support included"

---

## Results and Impact (1 minute)

"SeekerScholar delivers impressive performance:

- **Speed**: Most searches complete in under 200 milliseconds
- **Accuracy**: Hybrid method combines the strengths of all approaches
- **Scalability**: 2-stage pipeline handles large datasets efficiently
- **User Experience**: Clean interface with instant feedback

The system successfully bridges the gap between traditional keyword search and modern semantic search, while maintaining the speed users expect. Researchers can now find relevant papers faster, whether they're looking for specific terms, conceptual ideas, or authoritative sources."

---

## Challenges and Solutions (1 minute)

"During development, we faced several challenges:

**Challenge 1: Speed with Large Datasets**
- Problem: Processing 160,000 papers with neural models would be too slow
- Solution: 2-stage pipeline with BM25 candidate generation

**Challenge 2: Long Query Performance**
- Problem: Long abstracts or PDFs slow down neural models
- Solution: Query truncation and first-100-words optimization for PDFs

**Challenge 3: Memory Management**
- Problem: Loading all embeddings and models into memory
- Solution: Efficient precomputation and single-load architecture

**Challenge 4: User Experience**
- Problem: Long searches feel unresponsive
- Solution: Cancel functionality, loading indicators, and smart caching"

---

## Future Enhancements (30 seconds)

"Potential future improvements include:

- **Multi-language support** for international papers
- **Citation network visualization** to explore paper relationships
- **Saved searches and favorites** for user accounts
- **Advanced filters** by date, category, or author
- **Recommendation system** based on search history
- **Export functionality** to save search results"

---

## Conclusion (30 seconds)

"In conclusion, SeekerScholar demonstrates how combining traditional information retrieval with modern machine learning can create a powerful, fast, and user-friendly search system. The 2-stage pipeline architecture ensures speed, while multiple search methods provide flexibility for different use cases.

Whether you're a researcher looking for specific papers, exploring a new field, or finding similar work to your own, SeekerScholar makes academic paper discovery faster and more intuitive.

Thank you for your attention. I'm happy to answer any questions!"

---

## Q&A Preparation

**Potential Questions and Answers:**

**Q: How does the scoring work?**
A: Each method calculates scores differently. BM25 uses keyword matching, BERT uses cosine similarity between embeddings, PageRank combines keyword relevance with citation authority, and Hybrid normalizes and weights all three. Higher scores mean better relevance.

**Q: Why 300 candidates in Stage 1?**
A: We found 300 to be the sweet spot - large enough to include relevant papers, small enough to keep Stage 2 fast. This can be tuned based on performance requirements.

**Q: Can it handle other datasets?**
A: Yes! The architecture is dataset-agnostic. You just need to provide the precomputed artifacts: DataFrame, BM25 index, embeddings, and citation graph.

**Q: What about papers not in the dataset?**
A: Currently, SeekerScholar searches only the precomputed ogbn-arxiv dataset. To add new papers, you'd need to regenerate the indices and embeddings.

**Q: How accurate is the search?**
A: The Hybrid method provides the best balance, combining keyword matching, semantic understanding, and authority. BERT excels at finding conceptually similar papers even with different terminology.

**Q: Can users customize the hybrid weights?**
A: Currently, weights are set in configuration (30% BM25, 50% BERT, 20% PageRank). This could be made user-configurable in a future version.

**Q: How were the hybrid weights determined?**
A: The weights are heuristic choices based on information retrieval best practices:
- **BERT (50%)**: Semantic understanding is often the most valuable for academic search, as researchers look for conceptually similar work, not just keyword matches
- **BM25 (30%)**: Provides a solid baseline ensuring exact term matches are still prioritized
- **PageRank (20%)**: Adds authority signals without overwhelming relevance - we want relevant papers first, then boost influential ones
- All scores are normalized to [0,1] before combining to ensure fair contribution
- These could be tuned further using evaluation metrics like precision@k, recall@k, or user feedback

---

## Presentation Tips

1. **Timing**: Total script is ~12-15 minutes. Adjust sections based on your time limit.

2. **Visual Aids**: 
   - Show the UI during demo section
   - Consider slides for architecture diagram
   - Show code snippets for technical audience

3. **Pacing**: 
   - Speak clearly and pause between sections
   - Emphasize key points (2-stage pipeline, performance numbers)
   - Slow down during technical explanations

4. **Engagement**:
   - Ask rhetorical questions: "How do we make neural search fast?"
   - Use analogies: "Think of Stage 1 as a filter, Stage 2 as refinement"
   - Show enthusiasm about the performance numbers

5. **Adaptation**:
   - For technical audience: Focus more on architecture and optimizations
   - For general audience: Focus more on features and user experience
   - For business audience: Emphasize speed, scalability, and impact

6. **Practice**: 
   - Read through 2-3 times before presenting
   - Time yourself
   - Mark sections to skip if running short on time

---

**Good luck with your presentation! 🎤**

