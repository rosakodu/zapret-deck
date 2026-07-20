import asyncio
import aiohttp
import json
import sys

async def main():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://localhost:8080/json') as resp:
                tabs = await resp.json()
        except Exception as e:
            print(f"Failed to connect to CEF debugger: {e}")
            return

        ws_url = None
        for tab in tabs:
            if tab.get('title') == 'SharedJSContext':
                ws_url = tab.get('webSocketDebuggerUrl')
                break
        
        if not ws_url:
            print("SharedJSContext not found in tabs:")
            print(json.dumps(tabs, indent=2))
            return

        print(f"Connecting to debug WebSocket: {ws_url}")
        async with session.ws_connect(ws_url) as ws:
            await ws.send_json({"id": 1, "method": "Console.enable"})
            await ws.send_json({"id": 2, "method": "Runtime.enable"})
            await ws.send_json({"id": 3, "method": "Log.enable"})
            
            print("Listening for CEF logs (press Ctrl+C to exit)...")
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    method = data.get("method")
                    params = data.get("params", {})
                    
                    if method == "Runtime.exceptionThrown":
                        details = params.get("exceptionDetails", {})
                        text = details.get("text", "")
                        exception = details.get("exception", {})
                        description = exception.get("description", "")
                        print(f"\n[EXCEPTION] {text} - {description}")
                    elif method == "Console.messageAdded":
                        message = params.get("message", {})
                        level = message.get("level")
                        text = message.get("text")
                        url = message.get("url", "")
                        line = message.get("line", "")
                        print(f"[CONSOLE][{level}] {text} ({url}:{line})")
                    elif method == "Log.entryAdded":
                        entry = params.get("entry", {})
                        print(f"[LOG][{entry.get('level')}] {entry.get('text')}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
