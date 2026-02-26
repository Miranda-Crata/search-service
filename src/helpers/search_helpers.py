from src.settings import RRF_K


def hybrid_search(conn, query_text, query_embedding, project_id=None, limit=5):
    bm25_results = _bm25_search(conn, query_text, project_id)
    vector_results = _vector_search(conn, query_embedding, project_id)
    fused = _reciprocal_rank_fusion(bm25_results, vector_results, k=RRF_K, limit=limit)
    return fused


def _bm25_search(conn, query_text, project_id=None):
    sql = """
        SELECT dc.id, dc.document_id, dc.content, dc.chunk_order,
               dc.page_start, dc.page_end, dc.contextualization,
               d.name AS document_name, d.project_id,
               ts_rank_cd(dc.search_vector, plainto_tsquery('spanish', %(query)s)) AS bm25_score
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE dc.search_vector @@ plainto_tsquery('spanish', %(query)s)
          AND d.status_key = 'ready'
          AND dc.embedded = true
          AND (%(project_id)s IS NULL OR d.project_id = %(project_id)s::uuid)
        ORDER BY bm25_score DESC
        LIMIT 20
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"query": query_text, "project_id": project_id})
        return cur.fetchall()


def _vector_search(conn, query_embedding, project_id=None):
    sql = """
        SELECT dc.id, dc.document_id, dc.content, dc.chunk_order,
               dc.page_start, dc.page_end, dc.contextualization,
               d.name AS document_name, d.project_id,
               1 - (dc.embedding <=> %(embedding)s::vector) AS vector_score
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE dc.embedded = true
          AND d.status_key = 'ready'
          AND (%(project_id)s IS NULL OR d.project_id = %(project_id)s::uuid)
        ORDER BY dc.embedding <=> %(embedding)s::vector
        LIMIT 20
    """
    with conn.cursor() as cur:
        cur.execute(sql, {"embedding": str(query_embedding), "project_id": project_id})
        return cur.fetchall()


def _reciprocal_rank_fusion(bm25_results, vector_results, k=60, limit=5):
    scores = {}

    for rank, row in enumerate(bm25_results):
        chunk_id = str(row["id"])
        scores[chunk_id] = {
            "data": row,
            "score": 1 / (k + rank + 1),
        }

    for rank, row in enumerate(vector_results):
        chunk_id = str(row["id"])
        if chunk_id in scores:
            scores[chunk_id]["score"] += 1 / (k + rank + 1)
        else:
            scores[chunk_id] = {
                "data": row,
                "score": 1 / (k + rank + 1),
            }

    sorted_results = sorted(scores.values(), key=lambda x: x["score"], reverse=True)

    return [
        _format_result(entry["data"], entry["score"])
        for entry in sorted_results[:limit]
    ]


def _format_result(row, score):
    return {
        "chunkId": str(row["id"]),
        "documentId": str(row["document_id"]),
        "documentName": row["document_name"],
        "projectId": str(row["project_id"]),
        "content": row["content"],
        "contextualization": row["contextualization"],
        "chunkOrder": row["chunk_order"],
        "pageStart": row["page_start"],
        "pageEnd": row["page_end"],
        "score": round(score, 6),
    }
