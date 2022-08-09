from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    DISCORD_TOKEN: str
    DEFAULT_PREFIX: str

    SUCCESS_EMOJI: str
    FAILURE_EMOJI: str

    VERSION: str
    SUPPORT_LINK: str

    socks5_proxy_url: Optional[str]
    use_socks5_for_all_connections: bool
    user_agent: str
    ec_api_base_url: Optional[str]
    http_head_timeout: int
    http_read_timeout: int
