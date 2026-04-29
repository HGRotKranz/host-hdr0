# meta developer: @Huai_Baike
# meta syntax: .gpt <питання>

__version__ = (2, 0, 1)

import asyncio
import logging
import re
import time

import aiohttp
from .. import loader, utils

logger = logging.getLogger(__name__)


def _md_to_html(text: str) -> str:
    """Конвертує markdown-форматування в HTML-теги Telegram."""
    # Багаторядкові блоки коду з мовою: ```python\n...\n```
    text = re.sub(
        r"```(\w+)?\n?(.*?)```",
        lambda m: f"<pre><code>{m.group(2).strip()}</code></pre>",
        text,
        flags=re.DOTALL,
    )
    # Інлайн-код
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # **жирний** і __жирний__
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: f"<b>{m.group(1) or m.group(2)}</b>", text)
    # *курсив* і _курсив_
    text = re.sub(r"\*(.+?)\*|_(.+?)_", lambda m: f"<i>{m.group(1) or m.group(2)}</i>", text)
    return text.strip()


@loader.tds
class MyGemmaGPT(loader.Module):
    """Gemma 3 Local & Cloud AI Connector"""

    strings = {
        "name": "MyGemmaGPT",
        "no_args": (
            "<b><emoji document_id=5312526098750252863>🚫</emoji>"
            " Напиши питання після команди!</b>"
        ),
        "loading": (
            "<b><emoji document_id=5974038293120027938>👤</emoji> Питання:</b> {question}\n"
            "<code>⏳ Опрацьовую...</code>"
        ),
        "answer": (
            "<b><emoji document_id=5974038293120027938>👤</emoji> Питання:</b> {question}\n"
            "<b><emoji document_id=5199682846729449178>🤖</emoji> Відповідь:</b>\n{answer}"
        ),
        "error": (
            "<b><emoji document_id=5312526098750252863>🚫</emoji>"
            " Помилка:</b> <code>{error}</code>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                "local",
                "API Key (для Ollama — будь-який текст)",
                validator=loader.validators.Hidden(loader.validators.String()),
            ),
            loader.ConfigValue(
                "api_url",
                "http://localhost:11434/v1",
                "Base URL (Ollama: http://localhost:11434/v1)",
            ),
            loader.ConfigValue(
                "model",
                "gemma3:4b",
                "Назва моделі (gemma3:4b, llama3.1:8b тощо)",
            ),
            loader.ConfigValue(
                "system_prompt",
                "Ти — жива людина, відповідай коротко і природно українською.",
                "Системний промпт для ШІ",
            ),
            loader.ConfigValue("max_tokens", 512, "Ліміт токенів відповіді"),
            loader.ConfigValue("timeout", 90, "Таймаут запиту (секунди)"),
        )
        self._session: aiohttp.ClientSession | None = None

    async def client_ready(self, client, db):
        self._session = aiohttp.ClientSession()

    async def on_unload(self):
        if self._session:
            await self._session.close()

    # ── AI ────────────────────────────────────────────────────────────────

    async def _ask(self, prompt: str) -> str:
        url = f"{self.config['api_url'].rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.config['api_key']}"}
        payload = {
            "model": self.config["model"],
            "max_tokens": self.config["max_tokens"],
            "messages": [
                {"role": "system", "content": self.config["system_prompt"]},
                {"role": "user",   "content": prompt},
            ],
        }
        t0 = time.monotonic()
        try:
            timeout = aiohttp.ClientTimeout(total=self.config["timeout"])
            async with self._session.post(url, json=payload, headers=headers, timeout=timeout) as resp:
                data = await resp.json()

            logger.debug("MyGemmaGPT: відповідь за %.1fс", time.monotonic() - t0)

            if "error" in data:
                raise RuntimeError(data["error"].get("message", "unknown API error"))

            return data["choices"][0]["message"]["content"]

        except asyncio.TimeoutError:
            raise RuntimeError(f"таймаут ({self.config['timeout']}с)")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(str(e)) from e

    # ── Command ───────────────────────────────────────────────────────────

    @loader.command(ru_doc="<питання> — Запитати ШІ")
    async def gpt(self, message):
        """<питання> — Ask local AI"""
        args = utils.get_args_raw(message).strip()
        if not args:
            await utils.answer(message, self.strings["no_args"])
            return

        # Показуємо індикатор завантаження
        msg = await utils.answer(message, self.strings["loading"].format(question=args))

        try:
            raw = await self._ask(args)
            formatted = _md_to_html(raw)
            await utils.answer(msg, self.strings["answer"].format(question=args, answer=formatted))
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))