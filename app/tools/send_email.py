import os
import aiohttp

async def send_email(email: str, subject: str, body: str) -> bool:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            os.getenv("SEND_EMAIL", ""),
            json=[
                email,
                "email@email.com",
                subject,
                body
            ],
        ) as response:
            if not response.ok:
                print("ERROR", "Failed to send email.", response.status)
                return False
            if response.status != 200:
                print("ERROR", "Failed to send email.", response.status)
                return False
            text = await response.text()
            if text != "":
                print("ERROR", "Failed to send email.", text)
                return False
            return True