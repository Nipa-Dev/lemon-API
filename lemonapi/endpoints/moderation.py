"""
Under development, this file has no usage yet, please don't even try to use it.
"""


from fastapi import APIRouter

router = APIRouter()


class API:
    """
    A helper class for interacting with redis and moderating users.
    This does NOT work yet, it's under development.
    """

    def __init__(self):
        self.debug = False
        self.redis = None  # Redis(host="redis", port=6379, decode_responses=True)

        self.req = str | None  # ip address to ban

    async def ban_user(self, duration: int = 120):
        """Bans a user from using the API temporally, by default using 120 seconds."""
        self.redis.set(self.req, "banned", duration)

    async def unban_user(self):
        """When user gets unbanned they will have access to the API again."""
        self.redis.delete(self.req)

    async def key_exists(self, key: str) -> bool:
        """
        Check if the given key exists in the redis database.
        :param key: The key to be used in the
        redis database.
        :return: boolean.
        """
        exists = await self.redis.exists(key)
        return exists


banned = {}


@router.post("/ban/{ip}")
async def ban_user(ip: str):
    """Ban a user from using the API."""
    if ip not in banned:
        banned[ip] = True
        return {"message": f"User with IP {ip} banned."}


@router.delete("/unban/{ip}")
async def unban_user(ip: str):
    """Unban a user from using the API."""
    if ip in banned:
        banned[ip] = False
        return {"message": f"User with IP {ip} unbanned."}
    else:
        return {"message": "IP not found"}


@router.get("/check/{ip}")
async def check_user(ip: str):
    """Check if a user is banned or not."""
    return {"message": banned.get(ip, False)}


@router.get("/list")
async def list_banned():
    """List all banned users."""
    return banned


@router.get("/clear")
async def clear_banned():
    """Clear all banned users."""
    banned.clear()
    return {"message": "Cleared."}
