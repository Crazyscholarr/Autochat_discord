import yaml
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Config:
    class SETTINGS:
        def __init__(self, config):
            self.THREADS: int = config.get("THREADS", 1)
            self.ATTEMPTS: int = config.get("ATTEMPTS", 3)
            self.SHUFFLE_ACCOUNTS: bool = config.get("SHUFFLE_ACCOUNTS", True)
            self.ACCOUNTS_RANGE: List[int] = config.get("ACCOUNTS_RANGE", [0, 0])
            self.EXACT_ACCOUNTS_TO_USE: List[int] = config.get("EXACT_ACCOUNTS_TO_USE", [])
            self.RANDOM_INITIALIZATION_PAUSE: Tuple[int, int] = tuple(config.get("RANDOM_INITIALIZATION_PAUSE", [5, 10]))
            self.RANDOM_PAUSE_BETWEEN_ACCOUNTS: Tuple[int, int] = tuple(config.get("RANDOM_PAUSE_BETWEEN_ACCOUNTS", [5, 10]))
            self.PAUSE_BETWEEN_ATTEMPTS: Tuple[int, int] = tuple(config.get("PAUSE_BETWEEN_ATTEMPTS", [3, 5]))

    class AI_CHATTER:
        def __init__(self, config):
            self.GUILDS: List[dict] = config.get("GUILDS", [])
            self.PAUSE_BETWEEN_MESSAGES: Tuple[int, int] = tuple(config.get("PAUSE_BETWEEN_MESSAGES", [5, 10]))
            self.REPLY_PERCENTAGE: float = config.get("REPLY_PERCENTAGE", 50)
            self.LEAVE_GUILD: bool = config.get("LEAVE_GUILD", False)

    class CAPSOLVER:
        def __init__(self, config):
            self.API_KEY: str = config.get("API_KEY", "")

    class GROK:
        def __init__(self, config):
            self.MODEL: str = config.get("MODEL", "grok-3")
            self.API_KEYS: List[str] = config.get("API_KEYS", [])
            self.PROXY_FOR_GROK: str = config.get("PROXY_FOR_GROK", "")

    class PROXY:
        def __init__(self, config):
            self.TIMEOUT: int = config.get("TIMEOUT", 5)

    def __init__(self, config_path: str):
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        
        self.SETTINGS = self.SETTINGS(config.get("SETTINGS", {}))
        self.AI_CHATTER = self.AI_CHATTER(config.get("AI_CHATTER", {}))
        self.CAPSOLVER = self.CAPSOLVER(config.get("CAPSOLVER", {}))
        self.GROK = self.GROK(config.get("GROK", {}))
        self.PROXY = self.PROXY(config.get("PROXY", {}))