import csv
from loguru import logger

async def update_account(token: str, field: str, value: str):
    try:
        with open("accounts_status.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([token, field, value])
        logger.info(f"Cập nhật trạng thái tài khoản {token}: {field} = {value}")
    except Exception as e:
        logger.error(f"Không thể cập nhật tài khoản {token}: {e}")