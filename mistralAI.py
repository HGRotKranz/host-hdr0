# meta developer: @RotKranz
# meta syntax: .mistral | .mistralimg | .mistralagent | .mistralagentadd

__version__ = (3, 0, 0)

import asyncio
import base64
import collections
import io
import logging
import re
import time
from typing import Dict, List, Optional

import aiohttp
from .. import loader, utils

logger = logging.getLogger(__name__)

BASE_URL = "https://api.mistral.ai"

ROLE_USER      = "user"
ROLE_ASSISTANT = "assistant"

# Вбудовані інструменти агента
TOOL_WEB_SEARCH   = {"type": "web_search"}
TOOL_CODE_INTERP  = {"type": "code_interpreter"}
TOOL_IMAGE_GEN    = {"type": "image_generation"}
TOOL_WEB_PREMIUM  = {"type": "web_search_premium"}


def _md_to_html(text: str) -> str:
    text = re.sub(
        r"```(\w+)?\n?(.*?)```",
        lambda m: f"<pre><code>{m.group(2).strip()}</code></pre>",
        text, flags=re.DOTALL,
    )
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__",
                  lambda m: f"<b>{m.group(1) or m.group(2)}</b>", text)
    text = re.sub(r"\*(.+?)\*|_(.+?)_",
                  lambda m: f"<i>{m.group(1) or m.group(2)}</i>", text)
    return text.strip()


def _parse_conversation_output(data: dict) -> tuple[str, list[bytes]]:
    """
    Парсить ConversationResponse.
    Повертає (text, [image_bytes, ...]).
    Зображення повертаються як data:image/png;base64,... або URL.
    """
    texts: list[str] = []
    images: list[bytes] = []

    for output in data.get("outputs", []):
        content = output.get("content", "")
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            for chunk in content:
                ctype = chunk.get("type", "")
                if ctype == "text":
                    texts.append(chunk.get("text", ""))
                elif ctype == "image_url":
                    img = chunk.get("image_url", "")
                    url = img if isinstance(img, str) else img.get("url", "")
                    if url.startswith("data:"):
                        # base64 inline
                        b64 = url.split(",", 1)[-1]
                        images.append(base64.b64decode(b64))
                    elif url:
                        images.append(url.encode())  # зберігаємо URL як bytes
    return "\n".join(texts).strip(), images


@loader.tds
class MistralModule(loader.Module):
    """Mistral AI: чат, зображення, OCR, TTS, транскрипція, агент-режим, Mistral Agents."""

    strings = {
        "name": "MistralAI",
        "no_api_key":  "<b>🔑 Спочатку встанови API ключ у <code>.config MistralAI</code>!</b>",
        "no_args":     "<b>❌ Введи аргумент після команди!</b>",
        "loading":     "<b>⏳ Опрацьовую...</b>",
        "generating":  "<b>🎨 Генерую зображення...</b>",
        "error":       "<b>❌ Помилка:</b> <code>{error}</code>",
        # chat
        "chat_answer": (
            "<b>👤</b> {question}\n"
            "<b>🤖</b> {answer}\n\n"
            "<i>⚡ {model} • {time:.1f}с</i>"
        ),
        # image
        "img_caption": "🎨 <i>{prompt}</i>",
        "img_no_result": "<b>❌ Зображення не згенеровано. Спробуй інший промт.</b>",
        # agents (Mistral Platform)
        "agents_header":    "<b>🤖 Твої Mistral агенти:</b>\n\n",
        "agents_empty":     "<b>🤖 У тебе ще немає агентів на Mistral.</b>",
        "agent_created":    "✅ <b>Агент створено!</b>\nID: <code>{id}</code>\nНазва: <b>{name}</b>",
        "agent_deleted":    "🗑 <b>Агент видалено:</b> <code>{id}</code>",
        "agent_set":        "✅ <b>Поточний агент:</b> <code>{id}</code> (<b>{name}</b>)",
        "agent_unset":      "ℹ️ <b>Агент скинуто.</b> Використовується звичайна модель.",
        "agent_info":       (
            "<b>🤖 Агент:</b> <code>{id}</code>\n"
            "<b>Назва:</b> {name}\n"
            "<b>Модель:</b> {model}\n"
            "<b>Інструменти:</b> {tools}\n"
            "<b>Інструкція:</b>\n<i>{instructions}</i>"
        ),
        # режим-агент (автовідповідь)
        "autoagent_on":     "🤖 <b>Авто-агент увімкнено</b> у чаті <code>{chat}</code>",
        "autoagent_off":    "😴 <b>Авто-агент вимкнено</b> у чаті <code>{chat}</code>",
        "autoagent_list_empty": "<b>🤖 Авто-агент ніде не активний.</b>",
        "autoagent_list":   "<b>🤖 Активні авто-агент чати:</b>\n{chats}",
        "memory_cleared":   "🧹 <b>Пам'ять очищена</b> у чаті <code>{chat}</code>",
        # моделі
        "models_header":    "<b>📋 Доступні моделі:</b>\n\n",
        # ocr / tts / transcription
        "ocr_result":       "<b>📄 OCR:</b>\n\n{text}",
        "ocr_no_media":     "<b>❌ Відповідь на фото або PDF!</b>",
        "tts_generating":   "<b>🎙 Генерую голос...</b>",
        "tts_done":         "<b>🔊 Mistral TTS</b>",
        "transcription":    "<b>🎤 Транскрипція:</b>\n\n{text}",
        "no_audio":         "<b>❌ Відповідь на аудіо/голосове повідомлення!</b>",
        "moderation":       "<b>🛡 Модерація:</b>\nБезпечно: {safe}\nКатегорії: {cats}",
        "embed_result":     (
            "<b>🔢 Ембединги ({model}):</b>\n"
            "<code>Розмірність: {dim}</code>\n"
            "<code>Перші 5: {preview}</code>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            # ── Основні ───────────────────────────────────────
            loader.ConfigValue(
                "api_key", "",
                "Mistral API Key (https://console.mistral.ai)",
                validator=loader.validators.Hidden(loader.validators.String()),
            ),
            loader.ConfigValue(
                "chat_model", "mistral-large-latest",
                "Модель для .mistral (mistral-large-latest, codestral-latest, …)",
            ),
            loader.ConfigValue(
                "system_prompt",
                "Ти — корисний асистент. Відповідай чітко і зрозуміло.",
                "Системний промпт для .mistral",
            ),
            loader.ConfigValue("max_tokens", 1024, "Ліміт токенів"),
            loader.ConfigValue("timeout", 120, "Таймаут (с)"),
            # ── Авто-агент (watcher) ───────────────────────────
            loader.ConfigValue(
                "agent_system_prompt",
                (
                    "Ти — особистий асистент власника цього Telegram-акаунту. "
                    "Спілкуйся природно, як жива людина. "
                    "Відповідай коротко і по суті."
                ),
                "Промпт поведінки авто-агента (хто він, як поводиться)",
            ),
            loader.ConfigValue(
                "agent_model", "mistral-large-latest",
                "Модель для авто-агента",
            ),
            loader.ConfigValue(
                "agent_mistral_id", "",
                "ID Mistral-агента для авто-режиму (якщо порожньо — використовується модель+промпт)",
            ),
            loader.ConfigValue(
                "agent_history_limit", 50,
                "Глибина пам'яті авто-агента (повідомлень на чат/юзера)",
                validator=loader.validators.Integer(minimum=5, maximum=500),
            ),
            loader.ConfigValue(
                "agent_typing", True,
                "Показувати 'друкує...' перед відповіддю",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "agent_show_name_in_group", True,
                "Підписувати ім'я у групових чатах",
                validator=loader.validators.Boolean(),
            ),
            # ── Інші моделі ────────────────────────────────────
            loader.ConfigValue("ocr_model",            "mistral-ocr-latest",   "Модель OCR"),
            loader.ConfigValue("tts_model",            "mistral-tts-latest",   "Модель TTS"),
            loader.ConfigValue("tts_voice",            "fr:emma",              "Голос TTS (lang:name)"),
            loader.ConfigValue("transcription_model",  "voxtral-mini-2507",    "Модель транскрипції"),
            loader.ConfigValue("embed_model",          "mistral-embed",        "Модель ембединів"),
            # ── Генерація зображень ───────────────────────────
            loader.ConfigValue(
                "image_model", "mistral-large-latest",
                "Модель для генерації зображень (використовує image_generation tool)",
            ),
        )
        self._session: aiohttp.ClientSession | None = None
        self._me = None

        # авто-агент: {chat_id: True}
        self._auto_chats: Dict[int, bool] = {}
        # пам'ять: {chat_id: deque} або {chat_id: {user_id: deque}}
        self._memory: Dict[int, object] = {}
        # поточний активний Mistral-агент (platform agent)
        self._active_agent_id: Optional[str] = None
        self._active_agent_name: Optional[str] = None

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def client_ready(self, client, db):
        self._session = aiohttp.ClientSession()
        self._me = await client.get_me()
        saved = self.db.get("MistralAI", "auto_chats", [])
        self._auto_chats = {int(c): True for c in saved}
        self._active_agent_id   = self.db.get("MistralAI", "active_agent_id", "")   or None
        self._active_agent_name = self.db.get("MistralAI", "active_agent_name", "") or None

    async def on_unload(self):
        if self._session:
            await self._session.close()

    # ── Internal helpers ───────────────────────────────────────────────────

    def _h(self) -> dict:
        return {"Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"}

    def _to(self) -> aiohttp.ClientTimeout:
        return aiohttp.ClientTimeout(total=self.config["timeout"])

    def _ok(self) -> bool:
        return bool(self.config["api_key"].strip())

    def _save_auto(self):
        self.db.set("MistralAI", "auto_chats", list(self._auto_chats.keys()))

    def _save_active_agent(self):
        self.db.set("MistralAI", "active_agent_id",   self._active_agent_id   or "")
        self.db.set("MistralAI", "active_agent_name", self._active_agent_name or "")

    def _get_mem(self, chat_id: int, user_id: Optional[int] = None) -> collections.deque:
        lim = self.config["agent_history_limit"]
        if user_id is not None:
            if chat_id not in self._memory:
                self._memory[chat_id] = {}
            grp = self._memory[chat_id]
            if user_id not in grp:
                grp[user_id] = collections.deque(maxlen=lim)
            return grp[user_id]
        else:
            if chat_id not in self._memory:
                self._memory[chat_id] = collections.deque(maxlen=lim)
            return self._memory[chat_id]

    # ── Low-level HTTP ─────────────────────────────────────────────────────

    async def _post(self, path: str, payload: dict, headers: dict | None = None) -> dict:
        url = f"{BASE_URL}{path}"
        h = headers or self._h()
        try:
            async with self._session.post(url, json=payload, headers=h, timeout=self._to()) as r:
                data = await r.json()
            if "error" in data:
                err = data["error"]
                raise RuntimeError(err.get("message", str(err)) if isinstance(err, dict) else str(err))
            return data
        except asyncio.TimeoutError:
            raise RuntimeError(f"таймаут ({self.config['timeout']}с)")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(str(e)) from e

    async def _get(self, path: str) -> dict:
        url = f"{BASE_URL}{path}"
        async with self._session.get(url, headers=self._h(), timeout=self._to()) as r:
            return await r.json()

    async def _delete(self, path: str) -> dict:
        url = f"{BASE_URL}{path}"
        async with self._session.delete(url, headers=self._h(), timeout=self._to()) as r:
            return await r.json()

    async def _patch(self, path: str, payload: dict) -> dict:
        url = f"{BASE_URL}{path}"
        async with self._session.patch(url, json=payload, headers=self._h(), timeout=self._to()) as r:
            return await r.json()

    # ── API: Chat completions ──────────────────────────────────────────────

    async def _chat(self, prompt: str, model: str | None = None,
                    system: str | None = None) -> tuple[str, str, float]:
        m = model or self.config["chat_model"]
        sys = system if system is not None else self.config["system_prompt"]
        payload = {
            "model": m,
            "max_tokens": self.config["max_tokens"],
            "messages": [
                {"role": "system", "content": sys},
                {"role": ROLE_USER, "content": prompt},
            ],
        }
        t0 = time.monotonic()
        data = await self._post("/v1/chat/completions", payload)
        text = data["choices"][0]["message"]["content"]
        return text, data.get("model", m), time.monotonic() - t0

    async def _chat_history(self, history: collections.deque, new_msg: str,
                             label: str | None = None) -> str:
        """Чат з пам'яттю для авто-агента."""
        system = self.config["agent_system_prompt"]
        messages = [{"role": "system", "content": system}]
        messages.extend(list(history))
        content = f"[{label}]: {new_msg}" if label else new_msg
        messages.append({"role": ROLE_USER, "content": content})
        payload = {
            "model": self.config["agent_model"],
            "max_tokens": self.config["max_tokens"],
            "messages": messages,
        }
        data = await self._post("/v1/chat/completions", payload)
        return data["choices"][0]["message"]["content"]

    # ── API: Conversations (підтримує агентів + image_generation) ─────────

    async def _conversation(
        self,
        prompt: str,
        tools: list | None = None,
        agent_id: str | None = None,
        model: str | None = None,
        instructions: str | None = None,
    ) -> tuple[str, list[bytes]]:
        """
        Викликає /v1/conversations.
        Повертає (text, [image_bytes_or_url_bytes]).
        """
        payload: dict = {"inputs": prompt, "stream": False}
        if agent_id:
            payload["agent_id"] = agent_id
        elif model:
            payload["model"] = model
        if tools:
            payload["tools"] = tools
        if instructions:
            payload["instructions"] = instructions
        data = await self._post("/v1/conversations", payload)
        return _parse_conversation_output(data)

    async def _conversation_append(
        self,
        conversation_id: str,
        prompt: str,
    ) -> tuple[str, list[bytes]]:
        payload = {"inputs": prompt, "stream": False}
        data = await self._post(f"/v1/conversations/{conversation_id}", payload)
        return _parse_conversation_output(data)

    # ── API: Image generation (через Conversations API) ───────────────────

    async def _generate_image(self, prompt: str) -> tuple[str, list[bytes]]:
        """
        Генерує зображення через Conversations API з інструментом image_generation.
        Повертає (text_caption, [image_bytes]).
        """
        return await self._conversation(
            prompt=prompt,
            tools=[TOOL_IMAGE_GEN],
            model=self.config["image_model"],
        )

    # ── API: Platform Agents CRUD ─────────────────────────────────────────

    async def _agents_list(self) -> list:
        data = await self._get("/v1/agents?page_size=50")
        return data.get("data", [])

    async def _agent_get(self, agent_id: str) -> dict:
        return await self._get(f"/v1/agents/{agent_id}")

    async def _agent_create(self, name: str, model: str, instructions: str,
                             tools: list | None = None) -> dict:
        payload = {
            "name": name,
            "model": model,
            "instructions": instructions,
            "tools": tools or [],
        }
        return await self._post("/v1/agents", payload)

    async def _agent_update(self, agent_id: str, **kwargs) -> dict:
        return await self._patch(f"/v1/agents/{agent_id}", kwargs)

    async def _agent_delete(self, agent_id: str) -> dict:
        return await self._delete(f"/v1/agents/{agent_id}")

    # ── API: OCR ──────────────────────────────────────────────────────────

    async def _ocr_b64(self, data: bytes, mime: str) -> str:
        b64 = base64.b64encode(data).decode()
        doc = (
            {"type": "base64_document", "document_media_type": mime, "document_data": b64}
            if "pdf" in mime else
            {"type": "base64_image", "image_media_type": mime, "image_data": b64}
        )
        resp = await self._post("/v1/ocr", {"model": self.config["ocr_model"], "document": doc})
        return "\n\n---\n\n".join(p.get("markdown", "") for p in resp.get("pages", [])).strip()

    # ── API: Embeddings ───────────────────────────────────────────────────

    async def _embeddings(self, text: str) -> tuple[list, str]:
        data = await self._post("/v1/embeddings", {
            "model": self.config["embed_model"], "input": [text], "encoding_format": "float",
        })
        return data["data"][0]["embedding"], data.get("model", self.config["embed_model"])

    # ── API: TTS ──────────────────────────────────────────────────────────

    async def _tts(self, text: str) -> bytes:
        url = f"{BASE_URL}/v1/audio/speech"
        h = {"Authorization": f"Bearer {self.config['api_key']}", "Content-Type": "application/json"}
        payload = {"model": self.config["tts_model"], "voice": self.config["tts_voice"],
                   "input": text, "output_format": "pcm"}
        async with self._session.post(url, json=payload, headers=h, timeout=self._to()) as r:
            if r.status != 200:
                raise RuntimeError(f"TTS {r.status}: {(await r.text())[:200]}")
            raw = await r.read()
        # PCM → WAV
        rate, ch, bits = 24000, 1, 16
        buf = io.BytesIO()
        buf.write(b"RIFF"); buf.write((36 + len(raw)).to_bytes(4, "little"))
        buf.write(b"WAVEfmt "); buf.write((16).to_bytes(4, "little"))
        buf.write((1).to_bytes(2, "little")); buf.write(ch.to_bytes(2, "little"))
        buf.write(rate.to_bytes(4, "little")); buf.write((rate * ch * bits // 8).to_bytes(4, "little"))
        buf.write((ch * bits // 8).to_bytes(2, "little")); buf.write(bits.to_bytes(2, "little"))
        buf.write(b"data"); buf.write(len(raw).to_bytes(4, "little")); buf.write(raw)
        return buf.getvalue()

    # ── API: Transcription ────────────────────────────────────────────────

    async def _transcribe(self, audio: bytes, fname: str = "audio.ogg") -> str:
        url = f"{BASE_URL}/v1/audio/transcriptions"
        form = aiohttp.FormData()
        form.add_field("model", self.config["transcription_model"])
        form.add_field("file", audio, filename=fname, content_type="audio/ogg")
        async with self._session.post(
            url, data=form, headers={"Authorization": f"Bearer {self.config['api_key']}"},
            timeout=self._to()
        ) as r:
            d = await r.json()
        if "error" in d:
            raise RuntimeError(str(d["error"]))
        return d.get("text", "")

    # ── API: Moderation ───────────────────────────────────────────────────

    async def _moderate(self, text: str) -> dict:
        return await self._post("/v1/moderations", {"model": "mistral-moderation-latest", "input": text})

    # ── API: Models ───────────────────────────────────────────────────────

    async def _models(self) -> list:
        return (await self._get("/v1/models")).get("data", [])

    # ════════════════════════════════════════════════════════════════════════
    # WATCHER — авто-агент
    # ════════════════════════════════════════════════════════════════════════

    async def watcher(self, message):
        if not message or not hasattr(message, "sender_id"):
            return
        if not self._ok():
            return
        if self._me and message.sender_id == self._me.id:
            return

        chat_id = message.chat_id
        if chat_id not in self._auto_chats:
            return

        text = (message.raw_text or "").strip()
        if not text:
            return

        try:
            chat = await message.get_chat()
            is_group = hasattr(chat, "title")
        except Exception:
            is_group = False

        try:
            sender = await message.get_sender()
            sender_name = (
                getattr(sender, "first_name", "")
                or getattr(sender, "username", "")
                or str(message.sender_id)
            )
        except Exception:
            sender_name = str(message.sender_id)

        user_key = message.sender_id if is_group else None
        history = self._get_mem(chat_id, user_key)

        # Зберігаємо вхідне повідомлення
        history.append({"role": ROLE_USER, "content": text})

        label = sender_name if (is_group and self.config["agent_show_name_in_group"]) else None

        # Якщо є вибраний Mistral-агент або agent_id у конфігу — використовуємо Conversations API
        agent_id = (
            self._active_agent_id
            or (self.config["agent_mistral_id"].strip() or None)
        )

        try:
            if self.config["agent_typing"]:
                async with message.client.action(chat_id, "typing"):
                    if agent_id:
                        # Через Conversations API (stateless — передаємо всю history)
                        history_text = "\n".join(
                            f"{'User' if m['role'] == ROLE_USER else 'Assistant'}: {m['content']}"
                            for m in history
                        )
                        reply_text, images = await self._conversation(
                            prompt=history_text,
                            agent_id=agent_id,
                        )
                    else:
                        reply_text = await self._chat_history(history, text, label)
                        images = []
            else:
                if agent_id:
                    history_text = "\n".join(
                        f"{'User' if m['role'] == ROLE_USER else 'Assistant'}: {m['content']}"
                        for m in history
                    )
                    reply_text, images = await self._conversation(
                        prompt=history_text,
                        agent_id=agent_id,
                    )
                else:
                    reply_text = await self._chat_history(history, text, label)
                    images = []
        except RuntimeError as e:
            logger.error("MistralAI watcher error: %s", e)
            return

        history.append({"role": ROLE_ASSISTANT, "content": reply_text})

        # Відправляємо зображення, якщо є
        for img in images:
            if img.startswith(b"http"):
                await message.client.send_file(chat_id, img.decode(), reply_to=message.id)
            else:
                await message.client.send_file(
                    chat_id,
                    io.BytesIO(img),
                    reply_to=message.id,
                )

        if reply_text:
            await message.respond(_md_to_html(reply_text), parse_mode="html")

    # ════════════════════════════════════════════════════════════════════════
    # КОМАНДИ
    # ════════════════════════════════════════════════════════════════════════

    # ── Чат ───────────────────────────────────────────────────────────────

    @loader.command(ru_doc="<питання> — Запитати Mistral AI")
    async def mistral(self, message):
        """<питання> — Запитати Mistral AI"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        args = utils.get_args_raw(message).strip()
        if not args:
            return await utils.answer(message, self.strings["no_args"])

        # Якщо активний Mistral-агент — використовуємо Conversations API
        agent_id = self._active_agent_id or (self.config["agent_mistral_id"].strip() or None)

        msg = await utils.answer(message, self.strings["loading"])
        try:
            if agent_id:
                t0 = time.monotonic()
                text, images = await self._conversation(prompt=args, agent_id=agent_id)
                elapsed = time.monotonic() - t0
                model_label = f"agent:{agent_id[:8]}"
            else:
                text, model_label, elapsed = await self._chat(args)
                images = []

            # Надсилаємо зображення
            for img in images:
                if img.startswith(b"http"):
                    await message.client.send_file(message.peer_id, img.decode())
                else:
                    await message.client.send_file(message.peer_id, io.BytesIO(img))

            await utils.answer(
                msg,
                self.strings["chat_answer"].format(
                    question=args, answer=_md_to_html(text),
                    model=model_label, time=elapsed,
                ),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<модель> <питання> — Чат із конкретною моделлю")
    async def mistralm(self, message):
        """<модель> <питання> — Чат із конкретною моделлю"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        args = utils.get_args_raw(message).strip()
        if not args or " " not in args:
            return await utils.answer(message, "<b>❌ Формат:</b> <code>.mistralm &lt;модель&gt; &lt;текст&gt;</code>")
        model, _, prompt = args.partition(" ")
        msg = await utils.answer(message, self.strings["loading"])
        try:
            text, used, elapsed = await self._chat(prompt.strip(), model=model.strip())
            await utils.answer(
                msg,
                self.strings["chat_answer"].format(
                    question=prompt.strip(), answer=_md_to_html(text),
                    model=used, time=elapsed,
                ),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    # ── Генерація зображень ───────────────────────────────────────────────

    @loader.command(ru_doc="<промт> — Згенерувати зображення через Mistral")
    async def mistralimg(self, message):
        """<промт> — Генерація зображення (Mistral image_generation tool)"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        prompt = utils.get_args_raw(message).strip()
        if not prompt:
            return await utils.answer(message, self.strings["no_args"])

        msg = await utils.answer(message, self.strings["generating"])
        try:
            text, images = await self._generate_image(prompt)

            if not images:
                return await utils.answer(msg, self.strings["img_no_result"])

            caption = self.strings["img_caption"].format(prompt=prompt)
            for img in images:
                if img.startswith(b"http"):
                    await message.client.send_file(
                        message.peer_id, img.decode(), caption=caption, parse_mode="html"
                    )
                else:
                    await message.client.send_file(
                        message.peer_id, io.BytesIO(img), caption=caption, parse_mode="html"
                    )

            await msg.delete()
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    # ── Mistral Platform Agents ────────────────────────────────────────────

    @loader.command(ru_doc="— Список твоїх Mistral-агентів")
    async def mistralagents(self, message):
        """— Список агентів на Mistral Platform"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            agents = await self._agents_list()
            if not agents:
                return await utils.answer(msg, self.strings["agents_empty"])
            lines = []
            for a in agents:
                active = " ✅" if a["id"] == self._active_agent_id else ""
                tools = ", ".join(t.get("type", "?") for t in a.get("tools", [])) or "—"
                lines.append(
                    f"• <code>{a['id']}</code> — <b>{a.get('name', '?')}</b>{active}\n"
                    f"  <i>Модель: {a.get('model','?')} | Інструменти: {tools}</i>"
                )
            text = self.strings["agents_header"] + "\n".join(lines)
            if len(text) > 4096:
                text = text[:4090] + "\n..."
            await utils.answer(msg, text)
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<agent_id> — Вибрати активного Mistral-агента для .mistral та авто-режиму")
    async def mistraluse(self, message):
        """<agent_id> — Встановити активного Mistral-агента (або 'none' щоб скинути)"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        agent_id = utils.get_args_raw(message).strip()
        if not agent_id:
            return await utils.answer(message, self.strings["no_args"])

        if agent_id.lower() == "none":
            self._active_agent_id   = None
            self._active_agent_name = None
            self._save_active_agent()
            return await utils.answer(message, self.strings["agent_unset"])

        msg = await utils.answer(message, self.strings["loading"])
        try:
            info = await self._agent_get(agent_id)
            self._active_agent_id   = info["id"]
            self._active_agent_name = info.get("name", agent_id)
            self._save_active_agent()
            await utils.answer(
                msg,
                self.strings["agent_set"].format(id=info["id"], name=info.get("name", "?")),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<agent_id> — Інфо про Mistral-агента")
    async def mistralагentinfo(self, message):
        """<agent_id> — Детальна інформація про агента"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        agent_id = utils.get_args_raw(message).strip() or self._active_agent_id
        if not agent_id:
            return await utils.answer(message, self.strings["no_args"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            a = await self._agent_get(agent_id)
            tools = ", ".join(t.get("type", "?") for t in a.get("tools", [])) or "—"
            await utils.answer(
                msg,
                self.strings["agent_info"].format(
                    id=a["id"], name=a.get("name", "?"),
                    model=a.get("model", "?"), tools=tools,
                    instructions=a.get("instructions", "—") or "—",
                ),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<назва> | <модель> | <інструкція> | [tools] — Створити Mistral-агента")
    async def mistralcreate(self, message):
        """
        Створити нового Mistral-агента.
        Формат: <назва> | <модель> | <інструкція> | [web_search,image_generation,code_interpreter]
        Приклад: .mistralcreate MyBot | mistral-large-latest | Ти корисний бот | web_search,image_generation
        """
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        raw = utils.get_args_raw(message).strip()
        if not raw or "|" not in raw:
            return await utils.answer(
                message,
                "<b>❌ Формат:</b> <code>.mistralcreate Назва | модель | Інструкція | tool1,tool2</code>\n"
                "<b>Доступні tools:</b> <code>web_search</code>, <code>image_generation</code>, "
                "<code>code_interpreter</code>, <code>web_search_premium</code>",
            )
        parts = [p.strip() for p in raw.split("|")]
        name         = parts[0] if len(parts) > 0 else "My Agent"
        model        = parts[1] if len(parts) > 1 else self.config["chat_model"]
        instructions = parts[2] if len(parts) > 2 else ""
        tool_names   = [t.strip() for t in parts[3].split(",")] if len(parts) > 3 else []

        TOOL_MAP = {
            "web_search":         {"type": "web_search"},
            "image_generation":   {"type": "image_generation"},
            "code_interpreter":   {"type": "code_interpreter"},
            "web_search_premium": {"type": "web_search_premium"},
        }
        tools = [TOOL_MAP[t] for t in tool_names if t in TOOL_MAP]

        msg = await utils.answer(message, self.strings["loading"])
        try:
            agent = await self._agent_create(name, model, instructions, tools)
            await utils.answer(
                msg,
                self.strings["agent_created"].format(id=agent["id"], name=agent.get("name", name)),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<agent_id> — Видалити Mistral-агента")
    async def mistraldelete(self, message):
        """<agent_id> — Видалити агента з Mistral Platform"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        agent_id = utils.get_args_raw(message).strip()
        if not agent_id:
            return await utils.answer(message, self.strings["no_args"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            await self._agent_delete(agent_id)
            if self._active_agent_id == agent_id:
                self._active_agent_id   = None
                self._active_agent_name = None
                self._save_active_agent()
            await utils.answer(msg, self.strings["agent_deleted"].format(id=agent_id))
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    # ── Авто-агент (watcher) ────────────────────────────────────────────────

    @loader.command(ru_doc="— Увімкнути/вимкнути авто-агент у поточному чаті")
    async def mistralauto(self, message):
        """— Увімкнути/вимкнути авто-агент (ШІ відповідає замість тебе)"""
        chat_id = message.chat_id
        if chat_id in self._auto_chats:
            del self._auto_chats[chat_id]
            self._save_auto()
            await utils.answer(message, self.strings["autoagent_off"].format(chat=chat_id))
        else:
            self._auto_chats[chat_id] = True
            self._save_auto()
            await utils.answer(message, self.strings["autoagent_on"].format(chat=chat_id))

    @loader.command(ru_doc="— Список чатів з активним авто-агентом")
    async def mistralautolist(self, message):
        """— Список чатів де активний авто-агент"""
        if not self._auto_chats:
            return await utils.answer(message, self.strings["autoagent_list_empty"])
        lines = [f"• <code>{cid}</code>" for cid in self._auto_chats]
        await utils.answer(
            message,
            self.strings["autoagent_list"].format(chats="\n".join(lines)),
        )

    @loader.command(ru_doc="— Очистити пам'ять авто-агента у поточному чаті")
    async def mistralclear(self, message):
        """— Очистити пам'ять авто-агента"""
        chat_id = message.chat_id
        if chat_id in self._memory:
            del self._memory[chat_id]
        await utils.answer(message, self.strings["memory_cleared"].format(chat=chat_id))

    # ── Інструменти ────────────────────────────────────────────────────────

    @loader.command(ru_doc="— Список моделей Mistral")
    async def mistralmodels(self, message):
        """— Показати всі доступні моделі"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            models = await self._models()
            if not models:
                return await utils.answer(msg, "<b>❌ Моделі не знайдено.</b>")
            lines = []
            for m in sorted(models, key=lambda x: x.get("id", "")):
                caps = m.get("capabilities", {})
                tags = (
                    ("💬" if caps.get("completion_chat") else "") +
                    ("👁" if caps.get("vision") else "") +
                    ("🔧" if caps.get("function_calling") else "") +
                    ("🎯" if caps.get("fine_tuning") else "")
                )
                lines.append(f"• <code>{m.get('id','?')}</code> {tags}")
            text = self.strings["models_header"] + "\n".join(lines)
            if len(text) > 4096:
                text = text[:4090] + "\n..."
            await utils.answer(msg, text)
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="— OCR зображення або PDF (відповідь на медіа)")
    async def mistralocr(self, message):
        """— OCR зображення/PDF"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        reply = await message.get_reply_message()
        msg = await utils.answer(message, self.strings["loading"])
        try:
            if reply and reply.photo:
                result = await self._ocr_b64(await reply.download_media(bytes), "image/jpeg")
            elif reply and reply.document:
                mime = reply.document.mime_type or ""
                result = await self._ocr_b64(
                    await reply.download_media(bytes),
                    "application/pdf" if "pdf" in mime else "image/jpeg",
                )
            else:
                return await utils.answer(msg, self.strings["ocr_no_media"])
            output = self.strings["ocr_result"].format(text=result or "<i>(текст не знайдено)</i>")
            if len(output) > 4096:
                output = output[:4090] + "\n..."
            await utils.answer(msg, output)
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<текст> — Синтез мовлення (TTS)")
    async def mistralvoice(self, message):
        """<текст> — TTS"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        args = utils.get_args_raw(message).strip()
        if not args:
            return await utils.answer(message, self.strings["no_args"])
        msg = await utils.answer(message, self.strings["tts_generating"])
        try:
            wav = await self._tts(args)
            await message.client.send_file(
                message.peer_id, io.BytesIO(wav),
                voice_note=True, caption=self.strings["tts_done"],
                reply_to=message.reply_to_msg_id,
            )
            await msg.delete()
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="— Транскрипція аудіо (відповідь на аудіо)")
    async def mistraltranscribe(self, message):
        """— Транскрипція голосового/аудіо"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        reply = await message.get_reply_message()
        if not reply or not (reply.voice or reply.audio or reply.document):
            return await utils.answer(message, self.strings["no_audio"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            audio = await reply.download_media(bytes)
            fname = "audio.mp3" if reply.audio else "audio.ogg"
            text = await self._transcribe(audio, fname)
            await utils.answer(
                msg, self.strings["transcription"].format(text=text or "<i>(не розпізнано)</i>")
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<текст> — Ембединг тексту")
    async def mistralembed(self, message):
        """<текст> — Векторне представлення"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        args = utils.get_args_raw(message).strip()
        if not args:
            return await utils.answer(message, self.strings["no_args"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            vec, model = await self._embeddings(args)
            await utils.answer(
                msg, self.strings["embed_result"].format(
                    model=model, dim=len(vec),
                    preview=", ".join(f"{v:.4f}" for v in vec[:5]),
                ),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<текст> — Модерація тексту")
    async def mistralmod(self, message):
        """<текст> — Перевірити текст"""
        if not self._ok():
            return await utils.answer(message, self.strings["no_api_key"])
        args = utils.get_args_raw(message).strip()
        if not args:
            return await utils.answer(message, self.strings["no_args"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            data = await self._moderate(args)
            res = data.get("results", [{}])[0]
            flagged = res.get("flagged", False)
            active  = [k for k, v in res.get("categories", {}).items() if v]
            await utils.answer(
                msg, self.strings["moderation"].format(
                    safe="✅ Так" if not flagged else "🚫 Ні",
                    cats=", ".join(active) or "немає",
                ),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    # ── Довідка ────────────────────────────────────────────────────────────

    @loader.command(ru_doc="— Список команд")
    async def mistralhelp(self, message):
        """— Список усіх команд MistralAI"""
        active = (
            f"\n<b>🤖 Активний агент:</b> <code>{self._active_agent_id}</code> "
            f"(<b>{self._active_agent_name}</b>)"
            if self._active_agent_id else ""
        )
        await utils.answer(
            message,
            f"<b>🤖 MistralAI v3 — команди:</b>{active}\n\n"
            "<b>💬 Чат</b>\n"
            "<code>.mistral &lt;питання&gt;</code> — Чат (або через активного агента)\n"
            "<code>.mistralm &lt;модель&gt; &lt;питання&gt;</code> — Конкретна модель\n"
            "<code>.mistralmodels</code> — Список моделей\n\n"
            "<b>🎨 Зображення</b>\n"
            "<code>.mistralimg &lt;промт&gt;</code> — Генерація зображення\n\n"
            "<b>🤖 Mistral Platform Agents</b>\n"
            "<code>.mistralagents</code> — Список твоїх агентів\n"
            "<code>.mistraluse &lt;agent_id&gt;</code> — Вибрати активного агента\n"
            "<code>.mistraluse none</code> — Скинути агента\n"
            "<code>.mistralагentinfo [agent_id]</code> — Інфо про агента\n"
            "<code>.mistralcreate Назва | модель | Інструкція | tools</code> — Створити агента\n"
            "<code>.mistraldelete &lt;agent_id&gt;</code> — Видалити агента\n\n"
            "<b>👻 Авто-агент (відповідає замість тебе)</b>\n"
            "<code>.mistralauto</code> — Увімк/вимк у поточному чаті\n"
            "<code>.mistralautolist</code> — Список активних чатів\n"
            "<code>.mistralclear</code> — Очистити пам'ять\n\n"
            "<b>🛠 Інструменти</b>\n"
            "<code>.mistralocr</code> — OCR фото/PDF\n"
            "<code>.mistralvoice &lt;текст&gt;</code> — TTS\n"
            "<code>.mistraltranscribe</code> — Транскрипція аудіо\n"
            "<code>.mistralembed &lt;текст&gt;</code> — Ембединг\n"
            "<code>.mistralmod &lt;текст&gt;</code> — Модерація\n\n"
            "<i>⚙️ <code>.config MistralAI</code></i>",
        )
