import json
import logging
import uuid

from pydantic import ValidationError

from src.clients.db_client import get_connection
from src.clients.embedding_client import generate_embedding
from src.helpers.search_helpers import hybrid_search
from src.models.search_models import SearchInput
from src.utils.request_utils import parse_body
from src.utils.response_utils import build_error_response, build_success_response

logger = logging.getLogger(__name__)


def handler(event, context):
    try:

        ############ HANDLE LAMBDA INVOKE (NON-API-GATEWAY) ############
        if "body" not in event and "query" in event:
            body = event
        else:
            body = parse_body(event)

        ############ VALIDATE INPUT ############
        try:
            validated = SearchInput(**body)
        except ValidationError as e:
            errors = e.errors()
            messages = [f"{err['loc'][-1]}: {err['msg']}" for err in errors]
            return build_error_response("; ".join(messages), 400)

        ############ VALIDATE PROJECT ID FORMAT ############
        if validated.project_id:
            try:
                uuid.UUID(validated.project_id)
            except ValueError:
                return build_error_response("Invalid projectId format", 400)

        ############ GET DATABASE CONNECTION ############
        conn = get_connection()

        ############ GENERATE QUERY EMBEDDING ############
        query_embedding = generate_embedding(validated.query)

        ############ EXECUTE HYBRID SEARCH ############
        results = hybrid_search(
            conn=conn,
            query_text=validated.query,
            query_embedding=query_embedding,
            project_id=validated.project_id,
            limit=validated.limit,
        )

        ############ RETURN RESULTS ############
        return build_success_response({"data": results})

    except Exception:
        logger.exception("Unhandled error in search")
        return build_error_response("Internal server error", 500)
