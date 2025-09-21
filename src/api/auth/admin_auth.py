"""
管理API認証
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from ..config import settings

logger = logging.getLogger(__name__)

# HTTPベアラー認証スキーム
admin_security = HTTPBearer(auto_error=False)


async def verify_admin_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(admin_security)
) -> bool:
    """
    管理API用のAPIキー認証
    """
    if not credentials:
        logger.warning("管理API認証: 認証情報が提供されていません")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理API認証が必要です。APIキーを提供してください。",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if credentials.credentials != settings.ADMIN_API_KEY:
        logger.warning(f"管理API認証: 無効なAPIキー - {credentials.credentials[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無効なAPIキーです。",
            headers={"WWW-Authenticate": "Bearer"}
        )

    logger.info("管理API認証: 認証成功")
    return True


def get_admin_user():
    """
    管理者ユーザー情報を取得
    """
    return {
        "user_id": "admin",
        "role": "admin",
        "permissions": ["read", "write", "delete", "admin"]
    }


class AdminAuth:
    """
    管理API認証クラス
    """

    @staticmethod
    async def require_admin_auth(
        auth_result: bool = Depends(verify_admin_api_key)
    ):
        """
        管理者認証が必要なエンドポイント用のデコレータ
        """
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="管理者認証に失敗しました"
            )
        return auth_result

    @staticmethod
    def get_current_admin_user(
        auth_result: bool = Depends(verify_admin_api_key)
    ):
        """
        現在の管理者ユーザー情報を取得
        """
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="認証されていません"
            )
        return get_admin_user()