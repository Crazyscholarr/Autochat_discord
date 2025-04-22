import aiohttp
import asyncio
import random
from loguru import logger

class Capsolver:
    def __init__(self, index: int, capsolver_key: str, session, proxy: str):
        self.index = index
        self.capsolver_key = capsolver_key
        self.session = session
        self.proxy = proxy
        self.cache = {}  # Bộ nhớ đệm captcha

    async def solve_hcaptcha(self, url: str, captcha_rqdata: str, site_key: str, user_agent: str):
        with logger.contextualize(index=self.index):
            cache_key = f"{url}:{site_key}"
            if cache_key in self.cache:
                logger.info("Sử dụng captcha từ bộ nhớ đệm")
                return self.cache[cache_key], True

            try:
                logger.info("Đang giải hCaptcha với Capsolver...")
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "clientKey": self.capsolver_key,
                        "task": {
                            "type": "HCaptchaTaskProxyless",
                            "websiteURL": url,
                            "websiteKey": site_key,
                            "userAgent": user_agent,
                            "data": captcha_rqdata
                        }
                    }
                    async with session.post("https://api.capsolver.com/createTask", json=payload) as response:
                        task_data = await response.json()
                        task_id = task_data.get("taskId")
                        if not task_id:
                            logger.error(f"Capsolver không thể tạo nhiệm vụ: {task_data}")
                            return await self.fallback_2captcha(url, site_key, user_agent)

                    for _ in range(30):
                        async with session.post("https://api.capsolver.com/getTaskResult", json={"clientKey": self.capsolver_key, "taskId": task_id}) as response:
                            result = await response.json()
                            if result.get("status") == "ready":
                                solution = result.get("solution", {}).get("gRecaptchaResponse")
                                if solution:
                                    logger.success("Giải hCaptcha thành công với Capsolver")
                                    self.cache[cache_key] = solution
                                    return solution, True
                            await asyncio.sleep(2)
                    logger.warning("Capsolver hết thời gian, chuyển sang 2Captcha...")
                    return await self.fallback_2captcha(url, site_key, user_agent)
            except Exception as e:
                logger.error(f"Lỗi khi giải hCaptcha với Capsolver: {e}")
                return await self.fallback_2captcha(url, site_key, user_agent)

    async def fallback_2captcha(self, url: str, site_key: str, user_agent: str):
        with logger.contextualize(index=self.index):
            try:
                logger.info("Đang giải hCaptcha với 2Captcha...")
                async with aiohttp.ClientSession() as session:
                    params = {
                        "key": self.twocaptcha_key,
                        "method": "hcaptcha",
                        "sitekey": site_key,
                        "pageurl": url,
                        "json": 1
                    }
                    async with session.get("https://2captcha.com/in.php", params=params) as response:
                        result = await response.json()
                        if result.get("status") != 1:
                            logger.error(f"2Captcha không thể tạo nhiệm vụ: {result}")
                            return "", False
                        captcha_id = result.get("request")

                    for _ in range(30):
                        async with session.get(f"https://2captcha.com/res.php?key={self.twocaptcha_key}&action=get&id={captcha_id}&json=1") as response:
                            result = await response.json()
                            if result.get("status") == 1:
                                solution = result.get("request")
                                logger.success("Giải hCaptcha thành công với 2Captcha")
                                self.cache[f"{url}:{site_key}"] = solution
                                return solution, True
                            await asyncio.sleep(5)
                    logger.error("2Captcha hết thời gian")
                    return "", False
            except Exception as e:
                logger.error(f"Lỗi khi giải hCaptcha với 2Captcha: {e}")
                return "", False