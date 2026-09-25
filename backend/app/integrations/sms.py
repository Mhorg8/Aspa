"""SMS provider integration boundary.

The local provider deliberately keeps OTPs in process memory instead of logging
them. It is suitable for local development only and can be replaced by an
adapter for the production SMS vendor without changing the auth module.
"""

from typing import Protocol


class SmsProvider(Protocol):
    async def send_otp(self, phone_number: str, code: str) -> None: ...


class LocalSmsProvider:
    def __init__(self) -> None:
        self.sent_codes: dict[str, str] = {}

    async def send_otp(self, phone_number: str, code: str) -> None:
        self.sent_codes[phone_number] = code
