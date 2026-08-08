from prometheus_client import Counter, Histogram

RAG_REQUESTS_TOTAL = Counter("rag_requests_total", "Total RAG chat requests", ["status"])
RAG_REQUEST_LATENCY = Histogram("rag_request_latency_seconds", "End-to-end RAG request latency")
RAG_LLM_LATENCY = Histogram("rag_llm_latency_seconds", "LLM generation latency")
RAG_VECTOR_SEARCH_LATENCY = Histogram("rag_vector_search_latency_seconds", "Vector search latency")
RAG_GRAPH_SEARCH_LATENCY = Histogram("rag_graph_search_latency_seconds", "Graph search latency")
CACHE_HITS = Counter("rag_cache_hits_total", "Cache hits for chat responses")
CACHE_MISSES = Counter("rag_cache_misses_total", "Cache misses for chat responses")
DOCUMENT_INGESTION_TOTAL = Counter("document_ingestion_total", "Total document ingestion attempts")
DOCUMENT_INGESTION_FAILURES = Counter("document_ingestion_failures_total", "Total failed document ingestions")
