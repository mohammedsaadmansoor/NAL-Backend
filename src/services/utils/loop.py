import asyncio


def get_loop():
    try:
        loop = asyncio.get_running_loop()
    except Exception as e:
        print("going to create new loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop
