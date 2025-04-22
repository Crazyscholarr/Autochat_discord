from dataclasses import dataclass


@dataclass
class Account:
    index: int
    token: str
    proxy: str