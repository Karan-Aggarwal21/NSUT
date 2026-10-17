"""Offline synchronization service – handles batched records uploaded from local SQLite."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.schemas.sync import SyncPayload, SyncRecordStatus, SyncResponse
from app.services.session_service import create_session
from app.services.result_service import create_result
from app.services.personalized_service import (
    create_personalized_session,
    create_personalized_result,
)
from app.services.questionnaire_service import submit_questionnaire_response
from app.models.assessment_session import AssessmentSession
from app.models.activity_result import ActivityResult
from app.models.questionnaire_response import QuestionnaireResponse

logger = logging.getLogger(__name__)


def process_sync_batch(db: Session, user_id: uuid.UUID, payload: SyncPayload) -> SyncResponse:
    """Process a batch of offline synchronized records idempotently."""
    results: list[SyncRecordStatus] = []
    accepted_count = 0
    duplicate_count = 0
    error_count = 0

    # 1. Cognitive Assessment Sessions
    for session_data in payload.cognitive_sessions:
        client_id = session_data.client_session_id
        try:
            # Check if exists
            existing = (
                db.query(AssessmentSession)
                .filter(AssessmentSession.client_session_id == client_id)
                .first()
            )
            if existing:
                results.append(
                    SyncRecordStatus(
                        record_type="cognitive_session",
                        client_id=client_id,
                        status="duplicate",
                        server_id=str(existing.id),
                    )
                )
                duplicate_count += 1
                continue

            session_obj = create_session(db, user_id, session_data.model_dump())
            results.append(
                SyncRecordStatus(
                    record_type="cognitive_session",
                    client_id=client_id,
                    status="accepted",
                    server_id=str(session_obj.id),
                )
            )
            accepted_count += 1
        except Exception as e:
            db.rollback()
            logger.warning("Sync cognitive_session error: %s", str(e))
            results.append(
                SyncRecordStatus(
                    record_type="cognitive_session",
                    client_id=client_id,
                    status="error",
                    error=str(e),
                )
            )
            error_count += 1

    # 2. Cognitive Results
    for result_data in payload.cognitive_results:
        client_id = result_data.client_result_id
        try:
            if client_id:
                existing_res = (
                    db.query(ActivityResult)
                    .filter(ActivityResult.client_result_id == client_id)
                    .first()
                )
                if existing_res:
                    results.append(
                        SyncRecordStatus(
                            record_type="cognitive_result",
                            client_id=client_id,
                            status="duplicate",
                            server_id=str(existing_res.id),
                        )
                    )
                    duplicate_count += 1
                    continue

            res_obj = create_result(db, user_id, result_data.model_dump())
            results.append(
                SyncRecordStatus(
                    record_type="cognitive_result",
                    client_id=client_id,
                    status="accepted",
                    server_id=str(res_obj.id),
                )
            )
            accepted_count += 1
        except Exception as e:
            db.rollback()
            logger.warning("Sync cognitive_result error: %s", str(e))
            results.append(
                SyncRecordStatus(
                    record_type="cognitive_result",
                    client_id=client_id,
                    status="error",
                    error=str(e),
                )
            )
            error_count += 1

    # 3. Personalized Sessions
    for p_session in payload.personalized_sessions:
        client_id = p_session.client_session_id
        try:
            existing_ps = (
                db.query(AssessmentSession)
                .filter(AssessmentSession.client_session_id == client_id)
                .first()
            )
            if existing_ps:
                results.append(
                    SyncRecordStatus(
                        record_type="personalized_session",
                        client_id=client_id,
                        status="duplicate",
                        server_id=str(existing_ps.id),
                    )
                )
                duplicate_count += 1
                continue

            ps_obj = create_personalized_session(db, user_id, p_session.model_dump())
            results.append(
                SyncRecordStatus(
                    record_type="personalized_session",
                    client_id=client_id,
                    status="accepted",
                    server_id=str(ps_obj.id),
                )
            )
            accepted_count += 1
        except Exception as e:
            db.rollback()
            logger.warning("Sync personalized_session error: %s", str(e))
            results.append(
                SyncRecordStatus(
                    record_type="personalized_session",
                    client_id=client_id,
                    status="error",
                    error=str(e),
                )
            )
            error_count += 1

    # 4. Personalized Results
    for p_res in payload.personalized_results:
        client_id = p_res.client_result_id
        try:
            if client_id:
                existing_pres = (
                    db.query(ActivityResult)
                    .filter(ActivityResult.client_result_id == client_id)
                    .first()
                )
                if existing_pres:
                    results.append(
                        SyncRecordStatus(
                            record_type="personalized_result",
                            client_id=client_id,
                            status="duplicate",
                            server_id=str(existing_pres.id),
                        )
                    )
                    duplicate_count += 1
                    continue

            pres_obj = create_personalized_result(db, user_id, p_res.model_dump())
            results.append(
                SyncRecordStatus(
                    record_type="personalized_result",
                    client_id=client_id,
                    status="accepted",
                    server_id=str(pres_obj.id),
                )
            )
            accepted_count += 1
        except Exception as e:
            db.rollback()
            logger.warning("Sync personalized_result error: %s", str(e))
            results.append(
                SyncRecordStatus(
                    record_type="personalized_result",
                    client_id=client_id,
                    status="error",
                    error=str(e),
                )
            )
            error_count += 1

    # 5. Questionnaire Responses
    for idx, q_resp in enumerate(payload.questionnaire_responses):
        client_id = q_resp.client_submission_id
        q_identifier = (
            payload.questionnaire_ids[idx]
            if idx < len(payload.questionnaire_ids)
            else "memory-wellbeing-v1"
        )
        try:
            if client_id:
                existing_q = (
                    db.query(QuestionnaireResponse)
                    .filter(QuestionnaireResponse.client_submission_id == client_id)
                    .first()
                )
                if existing_q:
                    results.append(
                        SyncRecordStatus(
                            record_type="questionnaire_response",
                            client_id=client_id,
                            status="duplicate",
                            server_id=str(existing_q.id),
                        )
                    )
                    duplicate_count += 1
                    continue

            resp_obj = submit_questionnaire_response(
                db, user_id, q_identifier, q_resp.model_dump()
            )
            results.append(
                SyncRecordStatus(
                    record_type="questionnaire_response",
                    client_id=client_id,
                    status="accepted",
                    server_id=str(resp_obj.id),
                )
            )
            accepted_count += 1
        except Exception as e:
            db.rollback()
            logger.warning("Sync questionnaire_response error: %s", str(e))
            results.append(
                SyncRecordStatus(
                    record_type="questionnaire_response",
                    client_id=client_id,
                    status="error",
                    error=str(e),
                )
            )
            error_count += 1

    return SyncResponse(
        results=results,
        accepted_count=accepted_count,
        duplicate_count=duplicate_count,
        error_count=error_count,
    )
