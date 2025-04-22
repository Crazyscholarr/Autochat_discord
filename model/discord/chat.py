import asyncio
import random
import aiohttp
import json
from loguru import logger
from curl_cffi.requests import AsyncSession

from utils.config import Config
from utils.constants import Account
from prompts import REFERENCED_MESSAGES_SYSTEM_PROMPT, BATCH_MESSAGES_SYSTEM_PROMPT

async def get_grok_response(messages: list, config: Config, is_reply: bool = False) -> str:
    with logger.contextualize(index=0):
        for _ in range(5):
            try:
                async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=True)) as session:
                    api_key = random.choice(config.GROK.API_KEYS)
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9007 Chrome/91.0.4472.164 Electron/13.6.9 Safari/537.36",
                    }
                    system_prompt = REFERENCED_MESSAGES_SYSTEM_PROMPT if is_reply else BATCH_MESSAGES_SYSTEM_PROMPT
                    prompt = f"{system_prompt}\n\nRecent messages: {messages}"
                    payload = {
                        "model": config.GROK.MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                    }
                    async with session.post(
                        "https://api.x.ai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        proxy=f"http://{config.GROK.PROXY_FOR_GROK}" if config.GROK.PROXY_FOR_GROK else None,
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            content = data["choices"][0]["message"]["content"]
                            forbidden_words = [
                                "hi", "hello", "good day", "hey", "gm", "greetings", "howdy", "sup", "yo",
                                "what’s up", "what’s good", "wassup", "how are you doing", "how are you",
                                "how’s it going", "how’s everything", "how’s life", "how’s your day going",
                                "how’s your day been", "how have you been", "what’s new with you", "what’s happening"
                            ]
                            content_words = content.lower().split()
                            if any(word in forbidden_words for word in content_words):
                                logger.warning(f"Phản hồi chứa từ bị cấm: {content}. Thử lại")
                                continue
                            word_count = len(content_words)
                            if not (3 <= word_count <= 15):
                                logger.warning(f"Phản hồi có {word_count} từ, không hợp lệ: {content}. Thử lại")
                                continue
                            return content
                        else:
                            logger.error(f"Không thể lấy phản hồi từ Grok: {response.status} - {await response.text()}")
                            return ""
            except Exception as e:
                logger.error(f"Lỗi trong get_grok_response: {e}")
                return ""
        logger.error("Không thể tạo phản hồi hợp lệ sau 5 lần thử")
        return "hmmm ! 😄"

async def get_recent_messages(account: Account, config: Config, session: AsyncSession, proxies: list, guild_id: str, channel_id: str, limit: int = 3) -> list:
    with logger.contextualize(index=account.index):
        available_proxies = proxies + [""]
        for proxy in available_proxies:
            try:
                url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit={limit}"
                headers = {
                    "Authorization": account.token,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9007 Chrome/91.0.4472.164 Electron/13.6.9 Safari/537.36",
                }
                response = await session.get(
                    url, headers=headers, proxy=f"http://{proxy}" if proxy else None
                )
                if response.status_code == 200:
                    messages = response.json()
                    return messages
                else:
                    logger.error(f"Không thể lấy tin nhắn gần đây trong channel {channel_id}")
            except Exception as e:
                logger.error(f"Lỗi khi lấy tin nhắn gần đây trong channel {channel_id} : {e}")
        logger.error(f"Tất cả proxy thất bại khi lấy tin nhắn gần đây trong channel {channel_id}")
        return []

async def send_message(account: Account, config: Config, session: AsyncSession, proxies: list, guild_id: str, channel_id: str) -> tuple[bool, str]:
    with logger.contextualize(index=account.index):
        for retry in range(config.SETTINGS.ATTEMPTS):
            try:
                recent_messages = await get_recent_messages(account, config, session, proxies, guild_id, channel_id)
                message_contents = [msg["content"] for msg in recent_messages if msg["content"]]
                if not message_contents:
                    logger.warning(f"Không tìm thấy tin nhắn gần đây trong channel {channel_id}, dùng tin nhắn mặc định")
                    response_content = await get_grok_response(["General chat in a Discord channel"], config)
                    if not response_content:
                        response_content = "hmmm ! 😄"
                else:
                    response_content = await get_grok_response(message_contents, config)
                    if not response_content:
                        response_content = "hmmm ! 😄"

                url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
                headers = {
                    "Authorization": account.token,
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9007 Chrome/91.0.4472.164 Electron/13.6.9 Safari/537.36",
                }
                proxy = random.choice(proxies + [""]) if proxies else ""
                response = await session.post(
                    url, headers=headers, json={"content": response_content}, proxy=f"http://{proxy}" if proxy else None
                )
                if response.status_code in [200, 204]:
                    message_id = response.json().get("id")
                    logger.success(f"| Gửi tin nhắn trong channel {channel_id}: {response_content}")
                    return True, message_id
                elif response.status_code == 429:
                    error_data = json.loads(response.text)
                    retry_after = error_data.get("retry_after", 5)
                    logger.warning(f"| Bị giới hạn tốc độ trong channel {channel_id}, thử lại sau {retry_after}s")
                    await asyncio.sleep(retry_after)
                else:
                    logger.error(f"| Không thể gửi tin nhắn trong channel {channel_id}")
            except Exception as e:
                logger.error(f"| Lỗi gửi tin nhắn trong channel {channel_id}: {e}")
            await asyncio.sleep(random.randint(*config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS))
        return False, ""

async def reply_message(account: Account, config: Config, session: AsyncSession, proxies: list, guild_id: str, channel_id: str) -> tuple[bool, str]:
    with logger.contextualize(index=account.index):
        for retry in range(config.SETTINGS.ATTEMPTS):
            try:
                recent_messages = await get_recent_messages(account, config, session, proxies, guild_id, channel_id, limit=1)
                if not recent_messages:
                    logger.warning(f"| Không tìm thấy tin nhắn để trả lời trong channel {channel_id}, gửi tin nhắn mới")
                    return await send_message(account, config, session, proxies, guild_id, channel_id)
                
                last_message = recent_messages[0]["content"]
                response_content = await get_grok_response([last_message], config, is_reply=True)
                if not response_content:
                    response_content = "hmmm ! 😄"

                url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=1"
                headers = {
                    "Authorization": account.token,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9007 Chrome/91.0.4472.164 Electron/13.6.9 Safari/537.36",
                }
                proxy = random.choice(proxies + [""]) if proxies else ""
                response = await session.get(
                    url, headers=headers, proxy=f"http://{proxy}" if proxy else None
                )
                if response.status_code != 200:
                    logger.error(f"| Không thể lấy tin nhắn cuối trong channel {channel_id}")
                    return False, ""
                
                last_message_data = response.json()[0]
                reply_url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
                payload = {
                    "content": response_content,
                    "message_reference": {
                        "message_id": last_message_data["id"],
                        "channel_id": channel_id,
                        "guild_id": guild_id,
                    },
                }
                response = await session.post(
                    url=reply_url, headers=headers, json=payload, proxy=f"http://{proxy}" if proxy else None
                )
                if response.status_code in [200, 204]:
                    message_id = response.json().get("id")
                    logger.success(f"| Trả lời tin nhắn trong channel {channel_id}: {response_content}")
                    return True, message_id
                elif response.status_code == 429:
                    error_data = json.loads(response.text)
                    retry_after = error_data.get("retry_after", 5)
                    logger.warning(f"| Bị giới hạn tốc độ trong channel {channel_id}, thử lại sau {retry_after}s")
                    await asyncio.sleep(retry_after)
                else:
                    logger.error(f"| Không thể trả lời tin nhắn trong channel {channel_id}")
            except Exception as e:
                logger.error(f"| Lỗi trả lời tin nhắn trong channel {channel_id}: {e}")
            await asyncio.sleep(random.randint(*config.SETTINGS.PAUSE_BETWEEN_ATTEMPTS))
        return False, ""

async def check_and_respond_to_replies(account: Account, config: Config, session: AsyncSession, proxies: list, guild_id: str, channel_id: str, bot_message_id: str) -> bool:
    with logger.contextualize(index=account.index):
        try:
            recent_messages = await get_recent_messages(account, config, session, proxies, guild_id, channel_id, limit=10)
            for message in recent_messages:
                if "message_reference" in message and message["message_reference"].get("message_id") == bot_message_id:
                    reply_content = message["content"]
                    bot_message = None
                    for msg in recent_messages:
                        if msg["id"] == bot_message_id:
                            bot_message = msg["content"]
                            break
                    if not bot_message:
                        logger.warning(f"| Không tìm thấy tin nhắn gốc với ID {bot_message_id}")
                        continue
                    
                    logger.info(f" | Tìm thấy tin nhắn trả lời:  Bot: {bot_message} | Người dùng: {reply_content}")
                    
                    response_content = await get_grok_response([f"Bot: {bot_message}", f"User: {reply_content}"], config, is_reply=True)
                    if not response_content:
                        response_content = "hmmm ! 😄"

                    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
                    headers = {
                        "Authorization": account.token,
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9007 Chrome/91.0.4472.164 Electron/13.6.9 Safari/537.36",
                    }
                    proxy = random.choice(proxies + [""]) if proxies else ""
                    payload = {
                        "content": response_content,
                        "message_reference": {
                            "message_id": message["id"],
                            "channel_id": channel_id,
                            "guild_id": guild_id,
                        },
                    }
                    response = await session.post(
                        url, headers=headers, json=payload, proxy=f"http://{proxy}" if proxy else None
                    )
                    if response.status_code in [200, 204]:
                        logger.success(f"| Trả lời tin nhắn người dùng trong channel {channel_id}: {response_content}")
                        return True
                    elif response.status_code == 429:
                        error_data = json.loads(response.text)
                        retry_after = error_data.get("retry_after", 5)
                        logger.warning(f"| Bị giới hạn tốc độ trong channel {channel_id}, thử lại sau {retry_after}s")
                        await asyncio.sleep(retry_after)
                    else:
                        logger.error(f"| Không thể trả lời tin nhắn trong channel {channel_id}")
                        return False
            return False
        except Exception as e:
            logger.error(f"| Lỗi khi kiểm tra và trả lời tin nhắn trong channel {channel_id} : {e}")
            return False