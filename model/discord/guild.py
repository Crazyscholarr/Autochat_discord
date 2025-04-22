import aiohttp
import asyncio
import random
from loguru import logger
from curl_cffi.requests import AsyncSession

from utils.config import Config
from utils.constants import Account

async def join_guild(account: Account, config: Config, guild_id: str, capsolver, session: AsyncSession, proxies: list) -> bool:
    with logger.contextualize(index=account.index):
        for retry in range(config.SETTINGS.ATTEMPTS):
            try:
                url = f"https://discord.com/api/v9/guilds/{guild_id}/members/@me"
                headers = {
                    "Authorization": account.token,
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9007 Chrome/91.0.4472.164 Electron/13.6.9 Safari/537.36",
                }
                proxy = random.choice(proxies + [""]) if proxies else ""
                response = await session.put(
                    url, headers=headers, json={}, proxy=f"http://{proxy}" if proxy else None
                )
                if response.status_code in [200, 201, 204]:
                    logger.success(f"Tham gia guild {guild_id} thành công")
                    return True
                elif response.status_code == 429:
                    logger.warning("Bị giới hạn tốc độ khi tham gia guild, thử lại...")
                else:
                    logger.error(f"Không thể tham gia guild {guild_id}: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Lỗi khi tham gia guild {guild_id}: {e}")
            await asyncio.sleep(random.randint(*config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS))
        return False

async def check_if_token_in_guild(account: Account, config: Config, session: AsyncSession, guild_id: str) -> bool:
    with logger.contextualize(index=account.index):
        try:
            url = f"https://discord.com/api/v9/users/@me/guilds"
            headers = {
                "Authorization": account.token,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9007 Chrome/91.0.4472.164 Electron/13.6.9 Safari/537.36",
            }
            response = await session.get(
                url, headers=headers, proxy=f"http://{account.proxy}" if account.proxy else None
            )
            if response.status_code == 200:
                guilds = response.json()
                guild_ids = [guild["id"] for guild in guilds]
                if guild_id in guild_ids:
                    logger.success(f"Token đã ở trong guild {guild_id}")
                    return True
                return False
            else:
                logger.error(f"Không thể kiểm tra guild {guild_id}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra guild {guild_id}: {e}")
            return False

async def leave_guild(account: Account, config: Config, guild_id: str) -> bool:
    with logger.contextualize(index=account.index):
        for retry in range(config.SETTINGS.ATTEMPTS):
            try:
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=True)) as session:
                    url = f"https://discord.com/api/v9/users/@me/guilds/{guild_id}"
                    headers = {
                        "Authorization": account.token,
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9007 Chrome/91.0.4472.164 Electron/13.6.9 Safari/537.36",
                    }
                    async with session.delete(
                        url, headers=headers, proxy=f"http://{account.proxy}" if account.proxy else None
                    ) as response:
                        if response.status in [200, 204]:
                            logger.success(f"Rời guild {guild_id} thành công")
                            return True
                        else:
                            logger.error(f"Không thể rời guild {guild_id}: {response.status} - {await response.text()}")
            except Exception as e:
                logger.error(f"Lỗi khi rời guild {guild_id}: {e}")
            await asyncio.sleep(random.randint(*config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS))
        return False