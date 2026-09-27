import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
from app.services.auth_service import create_user

async def main():
    user = await create_user("admin", "changeme123", "Admin", full_name="Prototype Admin")
    print("Created:" if user else "Already exists:", user)

asyncio.run(main())