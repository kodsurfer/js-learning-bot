import aiohttp
import logging

PISTON_API_URL = "https://emkc.org/api/v2/piston/execute"

async def execute_code(code: str, language: str = "javascript", stdin: str = ""):
    """
    Отправляет код на выполнение в Piston API.
    Возвращает словарь с выводом или ошибкой.
    """
    payload = {
        "language": language,
        "version": "*",
        "files": [{"content": code}],
        "stdin": stdin,
        "args": [],
        "compile_timeout": 10000,
        "run_timeout": 3000
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(PISTON_API_URL, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "stdout": data.get("run", {}).get("stdout", ""),
                        "stderr": data.get("run", {}).get("stderr", ""),
                        "compile": data.get("compile", {}).get("stderr", "")
                    }
                else:
                    return {"error": f"API вернул статус {resp.status}"}
    except Exception as e:
        logging.error(f"Ошибка при выполнении кода: {e}")
        return {"error": str(e)}
