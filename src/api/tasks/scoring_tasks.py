"""
採点タスク（Celery）
"""
from celery import current_task
from typing import List, Dict, Any
import logging
import asyncio
from datetime import datetime

from ..celery_app import celery_app
from ..database import SessionLocal
from ..services.scoring_service import ScoringService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def batch_scoring(self, answer_ids: List[int]) -> Dict[str, Any]:
    """バッチ採点タスク"""
    task_id = self.request.id
    total_answers = len(answer_ids)
    processed = 0
    results = []
    errors = []

    logger.info(f"バッチ採点開始: task_id={task_id}, 対象件数={total_answers}")

    # プログレス更新
    current_task.update_state(
        state='PROGRESS',
        meta={'current': 0, 'total': total_answers, 'status': '採点開始'}
    )

    try:
        db = SessionLocal()
        service = ScoringService(db)

        for i, answer_id in enumerate(answer_ids):
            try:
                # 非同期採点の実行
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(service.evaluate_answer(answer_id))
                loop.close()

                results.append({
                    "answer_id": answer_id,
                    "status": "success",
                    "score": result.total_score,
                    "result_id": result.id
                })
                processed += 1

                # プログレス更新
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': processed,
                        'total': total_answers,
                        'status': f'採点中 ({processed}/{total_answers})'
                    }
                )

            except Exception as e:
                error_msg = f"answer_id={answer_id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"採点エラー: {error_msg}")

        db.close()

        # 完了
        final_result = {
            'task_id': task_id,
            'total': total_answers,
            'processed': processed,
            'errors': len(errors),
            'results': results,
            'error_details': errors,
            'completed_at': datetime.utcnow().isoformat()
        }

        logger.info(f"バッチ採点完了: task_id={task_id}, 成功={processed}, エラー={len(errors)}")
        return final_result

    except Exception as e:
        logger.error(f"バッチ採点致命的エラー: {e}")
        raise


@celery_app.task(bind=True)
def single_scoring(self, answer_id: int) -> Dict[str, Any]:
    """単一採点タスク"""
    task_id = self.request.id
    logger.info(f"単一採点開始: task_id={task_id}, answer_id={answer_id}")

    try:
        db = SessionLocal()
        service = ScoringService(db)

        # 非同期採点の実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(service.evaluate_answer(answer_id))
        loop.close()

        db.close()

        final_result = {
            'task_id': task_id,
            'answer_id': answer_id,
            'status': 'completed',
            'score': result.total_score,
            'result_id': result.id,
            'completed_at': datetime.utcnow().isoformat()
        }

        logger.info(f"単一採点完了: task_id={task_id}, score={result.total_score}")
        return final_result

    except Exception as e:
        logger.error(f"単一採点エラー: task_id={task_id}, error={e}")
        raise


@celery_app.task
def cleanup_old_results(days: int = 30) -> Dict[str, Any]:
    """古い採点結果のクリーンアップ"""
    logger.info(f"クリーンアップタスク開始: {days}日前のデータを削除")

    try:
        db = SessionLocal()
        # クリーンアップロジックを実装
        # 実際の本番環境では、適切な削除条件を設定

        db.close()

        return {
            'status': 'completed',
            'cleaned_records': 0,  # 実際の削除件数
            'completed_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"クリーンアップエラー: {e}")
        raise