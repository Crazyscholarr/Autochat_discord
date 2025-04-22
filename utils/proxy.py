import aiohttp
import asyncio
from loguru import logger

async def check_proxy(proxy: str, timeout: int = 5) -> bool:
    with logger.contextualize(index=0):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://discord.com", proxy=f"http://{proxy}", timeout=timeout) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Proxy {proxy} không hoạt động: {e}")
            return False

async def get_valid_proxies(proxy_list: list, timeout: int = 5) -> list:
    with logger.contextualize(index=0):
        tasks = [check_proxy(proxy, timeout) for proxy in proxy_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_proxies = [proxy for proxy, valid in zip(proxy_list, results) if valid]
        logger.info(f"Tìm thấy {len(valid_proxies)} proxy hoạt động trong số {len(proxy_list)}")
        return valid_proxies