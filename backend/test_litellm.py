import asyncio
import os
import litellm
from app.core.config import get_settings

settings = get_settings()

async def test():
    # litellm.set_verbose = True
    print("Testing with gemini/gemini-pro")
    try:
        res = await litellm.acompletion(
            model="gemini/gemini-pro",
            api_key=settings.gemini_api_key,
            messages=[{"role": "user", "content": "hi"}]
        )
        print(res)
    except Exception as e:
        print("ERROR1:", type(e), e)

if __name__ == "__main__":
    asyncio.run(test())
