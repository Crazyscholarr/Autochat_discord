import asyncio
import random
import selectors
from loguru import logger
import sys
from curl_cffi.requests import AsyncSession

from utils.config import Config
from utils.constants import Account
from utils.proxy import get_valid_proxies
from model.discord.auth import login_account
from model.discord.chat import send_message, reply_message, check_and_respond_to_replies
from model.discord.guild import join_guild, leave_guild, check_if_token_in_guild
from model.discord.token_checker import token_checker
from capsolver import Capsolver

# Cấu hình logger
logger.remove()
logger.add(
    sys.stdout,
    format="<cyan>[{time:HH:mm:ss} | {time:DD-MM-YYYY}]</cyan> <magenta>[Crazyscholar @ Discord]</magenta> | <level>{level}</level> | <yellow> Tài khoản - {extra[index]}</yellow> | {message}",
    colorize=True,
    level="DEBUG"
)

async def process_account(account: Account, config: Config, proxies: list):
    with logger.contextualize(index=account.index):
        session = AsyncSession()
        capsolver = Capsolver(account.index, config.CAPSOLVER.API_KEY, session, account.proxy)

        # Kiểm tra token
        is_valid, status = await token_checker(account, config, session)
        if not is_valid:
            logger.error(f"Token không hợp lệ hoặc {status}, bỏ qua")
            return

        # Đăng nhập tài khoản
        if not await login_account(account, config, session):
            logger.error("Đăng nhập thất bại")
            return

        # Chờ 5-30 giây để tải tin nhắn
        delay = random.randint(5, 30)
        logger.info(f"Chờ {delay} giây để tải tin nhắn")
        await asyncio.sleep(delay)

        # Chạy vô hạn cho đến khi bị ngắt
        while True:
            try:
                # Xử lý từng guild
                for guild_config in config.AI_CHATTER.GUILDS:
                    guild_id = guild_config["GUILD_ID"]
                    channel_ids = guild_config["CHANNEL_IDS"]

                    # Kiểm tra và tham gia guild nếu cần
                    if not await check_if_token_in_guild(account, config, session, guild_id):
                        if not await join_guild(account, config, guild_id, capsolver, session, proxies):
                            logger.error(f"Không thể tham gia guild {guild_id}, bỏ qua")
                            continue
                        else:
                            logger.success(f"Tham gia guild {guild_id} thành công, tiếp tục gửi tin nhắn")
                    else:
                        logger.info(f"Đã ở trong guild {guild_id}, tiếp tục gửi tin nhắn")

                    # Gửi tin nhắn trong các channel của guild
                    try:
                        num_messages = random.randint(*guild_config["MESSAGES_PER_ACCOUNT"])
                        for _ in range(num_messages):
                            channel_id = random.choice(channel_ids)  # Chọn ngẫu nhiên channel
                            message_id = None
                            if random.random() < config.AI_CHATTER.REPLY_PERCENTAGE / 100:
                                success, message_id = await reply_message(account, config, session, proxies, guild_id, channel_id)
                                if not success:
                                    logger.warning(f"Trả lời tin nhắn thất bại trong channel {channel_id}, thử gửi tin nhắn mới")
                                    success, message_id = await send_message(account, config, session, proxies, guild_id, channel_id)
                            else:
                                success, message_id = await send_message(account, config, session, proxies, guild_id, channel_id)
                                if not success:
                                    logger.warning(f"Gửi tin nhắn thất bại trong channel {channel_id}, thử trả lời tin nhắn")
                                    success, message_id = await reply_message(account, config, session, proxies, guild_id, channel_id)

                            # Kiểm tra xem có ai trả lời tin nhắn không
                            if success and message_id:
                                await check_and_respond_to_replies(account, config, session, proxies, guild_id, channel_id, message_id)

                            await asyncio.sleep(random.randint(*config.AI_CHATTER.PAUSE_BETWEEN_MESSAGES))
                    except Exception as e:
                        logger.error(f"Không thể gửi tin nhắn trong guild {guild_id}: {e}")

                    # Rời guild nếu LEAVE_GUILD bật
                    if config.AI_CHATTER.LEAVE_GUILD:
                        await leave_guild(account, config, guild_id)

                # Sau khi xử lý tất cả guild, chờ trước khi lặp lại
                await asyncio.sleep(random.randint(*config.AI_CHATTER.PAUSE_BETWEEN_MESSAGES))
            except KeyboardInterrupt:
                logger.info("Ngắt chương trình, dừng xử lý tài khoản")
                break

async def main():
    with logger.contextualize(index=0):
        # Đặt SelectorEventLoop cho Windows
        selector = selectors.SelectSelector()
        loop = asyncio.SelectorEventLoop(selector)
        asyncio.set_event_loop(loop)

        config = Config("config.yaml")
        accounts = []
        proxies = []

        # Đọc proxy từ proxies.txt
        try:
            with open("proxies.txt", "r", encoding="utf-8") as f:
                proxies = [line.strip() for line in f if line.strip()]
            proxies = await get_valid_proxies(proxies, config.PROXY.TIMEOUT)
        except FileNotFoundError:
            logger.warning("Không tìm thấy proxies.txt, chạy không dùng proxy")
            proxies = [""]

        # Đọc token từ accounts.txt
        try:
            with open("accounts.txt", "r", encoding="utf-8") as f:
                for idx, token in enumerate(f, 1):
                    token = token.strip()
                    proxy = random.choice(proxies) if proxies else ""
                    accounts.append(Account(index=idx, token=token, proxy=proxy))
        except FileNotFoundError:
            logger.error("Không tìm thấy accounts.txt, dừng chương trình")
            return

        # Xáo trộn tài khoản
        if config.SETTINGS.SHUFFLE_ACCOUNTS:
            random.shuffle(accounts)

        # Lọc tài khoản theo cấu hình
        if config.SETTINGS.ACCOUNTS_RANGE != [0, 0]:
            start, end = config.SETTINGS.ACCOUNTS_RANGE
            accounts = [acc for acc in accounts if start <= acc.index <= end]
        elif config.SETTINGS.EXACT_ACCOUNTS_TO_USE:
            accounts = [acc for acc in accounts if acc.index in config.SETTINGS.EXACT_ACCOUNTS_TO_USE]

        # Chạy đa luồng
        tasks = []
        try:
            for account in accounts:
                await asyncio.sleep(random.randint(7, 12))
                tasks.append(process_account(account, config, proxies))
                if len(tasks) >= config.SETTINGS.THREADS:
                    await asyncio.gather(*tasks)
                    tasks = []
                    await asyncio.sleep(random.randint(7, 12))
            if tasks:
                await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Ngắt chương trình, dừng tất cả tác vụ")
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("Hoàn thành xử lý tất cả tài khoản")

if __name__ == "__main__":
    asyncio.run(main())