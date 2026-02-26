# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the search-service.

## Overview

RAG search microservice for retrieving relevant document chunks. Uses hybrid search combining BM25 full-text search with pgvector cosine similarity, fused via Reciprocal Rank Fusion (RRF). Called by the chat-service via synchronous Lambda invoke.

## Commands

```bash
pip install -r requirements.txt

# Verify imports resolve
python -c "from src.lambdas.search import handler"
python -c "from src.models.search_models import SearchInput; SearchInput(query='test')"
```

## Architecture

### Lambda Functions

| Function | Method | Path | Handler | Timeout | Memory |
|----------|--------|------|---------|---------|--------|
| `search` | POST | `search` | `src.lambdas.search.handler` | 30s | 512MB |

### Directory Structure

```
src/
├── clients/
│   ├── db_client.py              # Reusable psycopg2 connection (warm Lambda reuse)
│   └── embedding_client.py       # Amazon Titan V2 query embedding via Bedrock
├── models/search_models.py       # Pydantic validation (SearchInput)
├── helpers/search_helpers.py     # Hybrid search: BM25 + vector + RRF fusion
├── lambdas/search.py             # Lambda handler (thin orchestration only)
└── utils/
    ├── request_utils.py          # API Gateway event body parsing
    └── response_utils.py         # CORS headers, JSON serializer
```

### Handler Pattern

Same as project-service: Lambda handlers contain ONLY step-by-step function calls separated by `############ COMMENT ############` blocks. All logic lives in helpers/utils/models.

### Search Pipeline

1. Parse and validate input (query, optional projectId, limit)
2. Generate query embedding via Amazon Titan V2 (1024-dim)
3. Run BM25 full-text search (PostgreSQL tsvector + ts_rank_cd)
4. Run vector similarity search (pgvector cosine distance)
5. Fuse results with Reciprocal Rank Fusion (k=60)
6. Return top-N chunks with scores

### Database

Uses `document_chunks` table with:
- `search_vector tsvector` — GIN-indexed, auto-populated by trigger from content + contextualization
- `embedding vector(1024)` — HNSW-indexed for cosine similarity

## Environment Variables

- `SUPABASE_DB_URL` — PostgreSQL connection string (from AWS SSM)
- `SUPABASE_USE_POOLER` — `'true'`

## Deployment

Deployed via Serverless Framework v3 with Docker images pushed to ECR (`miranda/search-service`).
