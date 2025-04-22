import asyncio
import random
from loguru import logger
from curl_cffi.requests import AsyncSession

from utils.config import Config
from utils.constants import Account
from utils.writer import update_account

async def token_checker(account: Account, config: Config, client: AsyncSession) -> tuple[bool, str]:
    with logger.contextualize(index=account.index):
        for retry in range(config.SETTINGS.ATTEMPTS):
            try:
                guilds_url = "https://discord.com/api/v9/users/@me/affinities/guilds"
                me_url = "https://discord.com/api/v9/users/@me"
                headers = {
                    "Authorization": account.token,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9007 Chrome/91.0.4472.164 Electron/13.6.9 Safari/537.36",
                }
                resp = await client.get(guilds_url, headers=headers)
                if resp.status_code in (401, 403):
                    logger.warning(f"Token bị khóa: {account.token}")
                    return False, "khóa"
                if resp.status_code in (200, 204):
                    response = await client.get(me_url, headers=headers)
                    flags_data = response.json()['flags'] - response.json()['public_flags']
                    if flags_data == 17592186044416:
                        logger.warning(f"Token bị cách ly: {account.token}")
                        await update_account(account.token, "TRẠNG THÁI", "CÁCH LY")
                        return False, "cách ly"
                    elif flags_data == 1048576:
                        logger.warning(f"Token bị đánh dấu spam: {account.token}")
                        await update_account(account.token, "TRẠNG THÁI", "SPAM")
                        return False, "spam"
                    elif flags_data == 17592186044416 + 1048576:
                        logger.warning(f"Token bị đánh dấu spam và cách ly: {account.token}")
                        await update_account(account.token, "TRẠNG THÁI", "SPAM VÀ CÁCH LY")
                        return False, "spam và cách ly"
                    logger.success("Token hoạt động tốt")
                    await update_account(account.token, "TRẠNG THÁI", "OK")
                    return True, ""
                else:
                    logger.error(f"Mã trạng thái không hợp lệ {resp.status_code} khi kiểm tra token")
            except Exception as err:
                random_sleep = random.randint(config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[0], config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS[1])
                logger.error(f"Không thể kiểm tra trạng thái token: {err}. Thử lại sau {random_sleep} giây...")
                await asyncio.sleep(random_sleep)
        await update_account(account.token, "TRẠNG THÁI", "KHÔNG XÁC ĐỊNH")
        return False, "không xác định"