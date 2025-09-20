"""
pytest設定とフィクスチャ
"""
import pytest
import asyncio
import httpx
from playwright.async_api import async_playwright


@pytest.fixture(scope="session")
def event_loop():
    """イベントループのスコープをセッション全体に設定"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def api_client():
    """API クライアント（セッション共有）"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        yield client


@pytest.fixture(scope="session")
async def browser():
    """ブラウザインスタンス（セッション共有）"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def page(browser):
    """新しいページ（テストごと）"""
    page = await browser.new_page()
    yield page
    await page.close()


# テスト設定
pytest_plugins = ["pytest_asyncio"]