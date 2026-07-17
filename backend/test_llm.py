import asyncio
import os
import litellm

async def test():
    key = "YOUR_API_KEY_HERE"
    try:
        res = await litellm.acompletion(
            model="gemini/gemini-1.5-flash",
            api_key=key,
            messages=[{"role": "user", "content": "hello"}]
        )
        print("1.5-flash Success:", res.choices[0].message.content)
    except Exception as e:
        print("1.5-flash Error:", e)

    try:
        res = await litellm.acompletion(
            model="gemini/gemini-2.0-flash",
            api_key=key,
            messages=[{"role": "user", "content": "hello"}]
        )
        print("2.0-flash Success:", res.choices[0].message.content)
    except Exception as e:
        print("2.0-flash Error:", e)

    try:
        res = await litellm.acompletion(
            model="gemini/gemini-2.5-flash",
            api_key=key,
            messages=[{"role": "user", "content": "hello"}]
        )
        print("2.5-flash Success:", res.choices[0].message.content)
    except Exception as e:
        print("2.5-flash Error:", e)

asyncio.run(test())
