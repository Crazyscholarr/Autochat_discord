import asyncio
import random
from loguru import logger
from curl_cffi.requests import AsyncSession
from dataclasses import dataclass

from utils.config import Config
from utils.constants import Account


@dataclass
class AccountInfo:
    id: str
    username: str


async def get_account_info(account: Account, config: Config, session: AsyncSession) -> AccountInfo | None:
    headers = {
        "Authorization": account.token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    }
    for retry in range(config.SETTINGS.ATTEMPTS):
        try:
            response = await session.get("https://discord.com/api/v9/users/@me", headers=headers)
            if response.status_code in [200, 204]:
                data = response.json()
                return AccountInfo(id=data["id"], username=data["username"])
            else:
                logger.error(f"{account.index} | Failed to get account info: {response.status_code}")
        except Exception as e:
            logger.error(f"{account.index} | Get account info error: {e}")
        
        await asyncio.sleep(random.randint(*config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS))
    
    return None