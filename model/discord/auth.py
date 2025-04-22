import asyncio
import random
from loguru import logger
from curl_cffi.requests import AsyncSession

from utils.config import Config
from utils.constants import Account

async def login_account(account: Account, config: Config, session: AsyncSession) -> bool:
    with logger.contextualize(index=account.index):
        for retry in range(config.SETTINGS.ATTEMPTS):
            try:
                headers = {
                    "Authorization": account.token,
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                }
                response = await session.get("https://discord.com/api/v9/users/@me", headers=headers)
                if response.status_code in [200, 204]:
                    logger.success("Đăng nhập thành công")
                    return True
                else:
                    logger.error(f"Đăng nhập thất bại: {response.status_code}")
            except Exception as e:
                logger.error(f"Lỗi đăng nhập: {e}")
            await asyncio.sleep(random.randint(*config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS))
        return False