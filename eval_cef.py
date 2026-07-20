import asyncio
import aiohttp
import json

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8080/json') as resp:
            tabs = await resp.json()

        ws_url = None
        for tab in tabs:
            if tab.get('title') == 'SharedJSContext':
                ws_url = tab.get('webSocketDebuggerUrl')
                break
        
        if not ws_url:
            print("SharedJSContext not found")
            return

        async with session.ws_connect(ws_url) as ws:
            await ws.send_json({
                "id": 100,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "JSON.stringify(window.DeckyPluginLoader.plugins.find(p => p.name === 'zapret-deck'))",
                    "returnByValue": True
                }
            })
            
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data.get("id") == 100:
                        result = data.get("result", {}).get("result", {})
                        print(result.get("value"))
                        break

if __name__ == '__main__':
    asyncio.run(main())
