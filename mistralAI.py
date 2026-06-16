# meta developer: @RotKranz
# meta syntax: .mistral <питання> | .mistralvoice <текст> | .mistralocr | .mistralmodels | .mistralagent

__version__ = (2, 0, 0)

import asyncio
import base64
import collections
import io
import logging
import re
import time
from typing import Dict, List

import aiohttp
from .. import loader, utils

logger = logging.getLogger(__name__)

BASE_URL = "https://api.mistral.ai"

# Типи ролей для пам'яті
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"


def _md_to_html(text: str) -> str:
    """Конвертує markdown у HTML-теги для Telegram."""
    text = re.sub(
        r"```(\w+)?\n?(.*?)```",
        lambda m: f"<pre><code>{m.group(2).strip()}</code></pre>",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(
        r"\*\*(.+?)\*\*|__(.+?)__",
        lambda m: f"<b>{m.group(1) or m.group(2)}</b>",
        text,
    )
    text = re.sub(
        r"\*(.+?)\*|_(.+?)_",
        lambda m: f"<i>{m.group(1) or m.group(2)}</i>",
        text,
    )
    return text.strip()


@loader.tds
class MistralModule(loader.Module):
    """Повноцінний Mistral AI — чат, OCR, TTS, транскрипція, ембединги, агент-режим."""

    strings = {
        "name": "MistralAI",
        "no_api_key": "<b>🔑 Спочатку встанови API ключ у налаштуваннях модуля!</b>",
        "no_args": "<b>❌ Введи аргумент після команди!</b>",
        "loading": "<b>⏳ Опрацьовую...</b>",
        "error": "<b>❌ Помилка:</b> <code>{error}</code>",
        # chat
        "chat_answer": (
            "<b>👤 Питання:</b> {question}\n"
            "<b>🤖 Відповідь:</b>\n{answer}\n\n"
            "<i>⚡ {model} • {time:.1f}с</i>"
        ),
        # моделі
        "models_header": "<b>📋 Доступні моделі Mistral:</b>\n\n",
        # ocr
        "ocr_result": "<b>📄 OCR результат:</b>\n\n{text}",
        "ocr_no_media": "<b>❌ Відповідь на повідомлення з фото або PDF-файлом!</b>",
        # embeddings
        "embed_result": (
            "<b>🔢 Ембединги ({model}):</b>\n"
            "<code>Розмірність: {dim}</code>\n"
            "<code>Перші 5: {preview}</code>"
        ),
        # tts
        "tts_generating": "<b>🎙 Генерую голос...</b>",
        "tts_done": "<b>🔊 Голосове повідомлення</b> (Mistral TTS)",
        # transcription
        "transcription_result": "<b>🎤 Транскрипція:</b>\n\n{text}",
        "transcription_no_audio": "<b>❌ Відповідь на голосове/аудіо повідомлення!</b>",
        # moderation
        "moderation_result": (
            "<b>🛡 Модерація:</b>\n"
            "Безпечно: {safe}\n"
            "Категорії: {categories}"
        ),
        # agent
        "agent_enabled": "🤖 <b>Агент-режим увімкнено</b> у чаті <code>{chat}</code>",
        "agent_disabled": "😴 <b>Агент-режим вимкнено</b> у чаті <code>{chat}</code>",
        "agent_list_empty": "<b>🤖 Агент-режим зараз ніде не активний.</b>",
        "agent_list_header": "<b>🤖 Активні агент-чати:</b>\n{chats}",
        "agent_memory_cleared": "🧹 <b>Пам'ять агента очищено</b> у чаті <code>{chat}</code>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            # ── Основні ──────────────────────────────────────────────────
            loader.ConfigValue(
                "api_key",
                "",
                "Mistral API Key (https://console.mistral.ai)",
                validator=loader.validators.Hidden(loader.validators.String()),
            ),
            loader.ConfigValue(
                "chat_model",
                "mistral-large-latest",
                "Модель для чату (mistral-large-latest, mistral-small-latest, codestral-latest тощо)",
            ),
            loader.ConfigValue(
                "system_prompt",
                "Ти — корисний асистент. Відповідай чітко і зрозуміло.",
                "Системний промпт для звичайного чату (.mistral)",
            ),
            loader.ConfigValue("max_tokens", 1024, "Ліміт токенів відповіді"),
            loader.ConfigValue("timeout", 120, "Таймаут запиту (секунди)"),
            # ── Агент-режим ───────────────────────────────────────────────
            loader.ConfigValue(
                "agent_system_prompt",
                (
                    "Ти — особистий асистент власника цього акаунту. "
                    "Спілкуйся природно, як жива людина. "
                    "Не розкривай, що ти ШІ, якщо тебе не запитують прямо. "
                    "Відповідай коротко і по суті."
                ),
                "Системний промпт агента (хто він, як поводиться)",
            ),
            loader.ConfigValue(
                "agent_model",
                "mistral-large-latest",
                "Модель для агент-режиму",
            ),
            loader.ConfigValue(
                "agent_history_limit",
                50,
                "Кількість повідомлень у пам'яті агента (на кожен чат/користувача)",
                validator=loader.validators.Integer(minimum=5, maximum=500),
            ),
            loader.ConfigValue(
                "agent_typing_delay",
                True,
                "Показувати 'друкує...' перед відповіддю агента",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "agent_show_name_in_group",
                True,
                "Показувати ім'я співрозмовника у груповому чаті при відповіді агента",
                validator=loader.validators.Boolean(),
            ),
            # ── Інші моделі ───────────────────────────────────────────────
            loader.ConfigValue(
                "ocr_model",
                "mistral-ocr-latest",
                "Модель для OCR",
            ),
            loader.ConfigValue(
                "tts_model",
                "mistral-tts-latest",
                "Модель для синтезу мовлення (TTS)",
            ),
            loader.ConfigValue(
                "tts_voice",
                "fr:emma",
                "Голос для TTS (формат lang:name, наприклад en:charlie, fr:emma)",
            ),
            loader.ConfigValue(
                "transcription_model",
                "voxtral-mini-2507",
                "Модель для транскрипції аудіо",
            ),
            loader.ConfigValue(
                "embed_model",
                "mistral-embed",
                "Модель для ембединів",
            ),
        )
        self._session: aiohttp.ClientSession | None = None
        self._me = None

        # {chat_id: True}  — чати де увімкнено агент-режим
        self._agent_chats: Dict[int, bool] = {}

        # Пам'ять агента:
        # Для приватних чатів: {chat_id: deque([{role, content}])}
        # Для групових:        {chat_id: {user_id: deque([{role, content}])}}
        self._agent_memory: Dict[int, object] = {}

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def client_ready(self, client, db):
        self._session = aiohttp.ClientSession()
        self._me = await client.get_me()
        # Відновлюємо список активних чатів з бази хікки
        saved = self.db.get("MistralAI", "agent_chats", [])
        self._agent_chats = {int(cid): True for cid in saved}

    async def on_unload(self):
        if self._session:
            await self._session.close()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }

    def _timeout(self) -> aiohttp.ClientTimeout:
        return aiohttp.ClientTimeout(total=self.config["timeout"])

    def _check_key(self) -> bool:
        return bool(self.config["api_key"].strip())

    def _save_agent_chats(self):
        self.db.set("MistralAI", "agent_chats", list(self._agent_chats.keys()))

    def _get_history(self, chat_id: int, user_id: int | None = None) -> collections.deque:
        """Повертає deque з пам'яттю для даного чату/юзера."""
        limit = self.config["agent_history_limit"]
        if user_id is not None:
            # Груповий чат — окрема пам'ять для кожного учасника
            if chat_id not in self._agent_memory:
                self._agent_memory[chat_id] = {}
            group_mem = self._agent_memory[chat_id]
            if user_id not in group_mem:
                group_mem[user_id] = collections.deque(maxlen=limit)
            return group_mem[user_id]
        else:
            # Приватний чат
            if chat_id not in self._agent_memory:
                self._agent_memory[chat_id] = collections.deque(maxlen=limit)
            return self._agent_memory[chat_id]

    def _push_message(self, history: collections.deque, role: str, content: str):
        history.append({"role": role, "content": content})

    async def _post(self, path: str, payload: dict, headers: dict | None = None) -> dict:
        url = f"{BASE_URL}{path}"
        h = headers or self._headers()
        t0 = time.monotonic()
        try:
            async with self._session.post(
                url, json=payload, headers=h, timeout=self._timeout()
            ) as resp:
                data = await resp.json()
            logger.debug("Mistral %s → %.1fs", path, time.monotonic() - t0)
            if "error" in data:
                msg = data["error"]
                if isinstance(msg, dict):
                    msg = msg.get("message", str(msg))
                raise RuntimeError(str(msg))
            return data
        except asyncio.TimeoutError:
            raise RuntimeError(f"таймаут ({self.config['timeout']}с)")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(str(e)) from e

    async def _get(self, path: str) -> dict:
        url = f"{BASE_URL}{path}"
        async with self._session.get(
            url, headers=self._headers(), timeout=self._timeout()
        ) as resp:
            return await resp.json()

    # ── API: Chat ──────────────────────────────────────────────────────────

    async def _chat(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
    ) -> tuple[str, str, float]:
        """Простий чат без пам'яті. Повертає (відповідь, модель, час)."""
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
        elapsed = time.monotonic() - t0
        text = data["choices"][0]["message"]["content"]
        return text, data.get("model", m), elapsed

    async def _chat_with_history(
        self,
        history: collections.deque,
        new_user_msg: str,
        sender_label: str | None = None,
    ) -> str:
        """Чат з контекстом пам'яті для агент-режиму."""
        model = self.config["agent_model"]
        system = self.config["agent_system_prompt"]

        # Формуємо список повідомлень: system + history + нове
        messages = [{"role": "system", "content": system}]
        messages.extend(list(history))

        # Якщо в групі — вказуємо хто пише
        content = new_user_msg
        if sender_label:
            content = f"[{sender_label}]: {new_user_msg}"

        messages.append({"role": ROLE_USER, "content": content})

        payload = {
            "model": model,
            "max_tokens": self.config["max_tokens"],
            "messages": messages,
        }
        data = await self._post("/v1/chat/completions", payload)
        return data["choices"][0]["message"]["content"]

    # ── API: OCR ───────────────────────────────────────────────────────────

    async def _ocr_base64(self, file_bytes: bytes, media_type: str) -> str:
        b64 = base64.b64encode(file_bytes).decode()
        if media_type == "application/pdf":
            doc = {
                "type": "base64_document",
                "document_media_type": media_type,
                "document_data": b64,
            }
        else:
            doc = {
                "type": "base64_image",
                "image_media_type": media_type,
                "image_data": b64,
            }
        payload = {"model": self.config["ocr_model"], "document": doc}
        data = await self._post("/v1/ocr", payload)
        pages = data.get("pages", [])
        return "\n\n---\n\n".join(p.get("markdown", "") for p in pages).strip()

    # ── API: Embeddings ────────────────────────────────────────────────────

    async def _embeddings(self, text: str) -> tuple[list, str]:
        payload = {
            "model": self.config["embed_model"],
            "input": [text],
            "encoding_format": "float",
        }
        data = await self._post("/v1/embeddings", payload)
        vec = data["data"][0]["embedding"]
        return vec, data.get("model", self.config["embed_model"])

    # ── API: TTS ───────────────────────────────────────────────────────────

    async def _tts(self, text: str) -> bytes:
        payload = {
            "model": self.config["tts_model"],
            "voice": self.config["tts_voice"],
            "input": text,
            "output_format": "pcm",
        }
        url = f"{BASE_URL}/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }
        async with self._session.post(
            url, json=payload, headers=headers, timeout=self._timeout()
        ) as resp:
            if resp.status != 200:
                err = await resp.text()
                raise RuntimeError(f"TTS error {resp.status}: {err[:200]}")
            raw = await resp.read()

        # PCM → WAV
        rate, channels, bits = 24000, 1, 16
        data_size = len(raw)
        buf = io.BytesIO()
        buf.write(b"RIFF")
        buf.write((36 + data_size).to_bytes(4, "little"))
        buf.write(b"WAVEfmt ")
        buf.write((16).to_bytes(4, "little"))
        buf.write((1).to_bytes(2, "little"))
        buf.write(channels.to_bytes(2, "little"))
        buf.write(rate.to_bytes(4, "little"))
        buf.write((rate * channels * bits // 8).to_bytes(4, "little"))
        buf.write((channels * bits // 8).to_bytes(2, "little"))
        buf.write(bits.to_bytes(2, "little"))
        buf.write(b"data")
        buf.write(data_size.to_bytes(4, "little"))
        buf.write(raw)
        return buf.getvalue()

    # ── API: Transcription ────────────────────────────────────────────────

    async def _transcribe(self, audio_bytes: bytes, filename: str = "audio.ogg") -> str:
        url = f"{BASE_URL}/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.config['api_key']}"}
        form = aiohttp.FormData()
        form.add_field("model", self.config["transcription_model"])
        form.add_field(
            "file", audio_bytes, filename=filename, content_type="audio/ogg"
        )
        async with self._session.post(
            url, data=form, headers=headers, timeout=self._timeout()
        ) as resp:
            data = await resp.json()
        if "error" in data:
            raise RuntimeError(str(data["error"]))
        return data.get("text", "")

    # ── API: Moderation ───────────────────────────────────────────────────

    async def _moderate(self, text: str) -> dict:
        payload = {"model": "mistral-moderation-latest", "input": text}
        return await self._post("/v1/moderations", payload)

    # ── API: Models ───────────────────────────────────────────────────────

    async def _list_models(self) -> list:
        data = await self._get("/v1/models")
        return data.get("data", [])

    # ════════════════════════════════════════════════════════════════════════
    # АГЕНТ-РЕЖИМ: watcher
    # ════════════════════════════════════════════════════════════════════════

    async def watcher(self, message):
        """Перехоплює повідомлення у агент-чатах і відповідає замість власника."""
        # Пропускаємо власні повідомлення та повідомлення без тексту
        if not message or not hasattr(message, "sender_id"):
            return
        if not self._check_key():
            return

        # Чи це наш акаунт? — пропускаємо
        if self._me and message.sender_id == self._me.id:
            return

        chat_id = message.chat_id
        if chat_id not in self._agent_chats:
            return

        text = message.raw_text or ""
        if not text.strip():
            return

        # Визначаємо чи це група
        try:
            chat = await message.get_chat()
            is_group = hasattr(chat, "title")  # Group/Channel мають title
        except Exception:
            is_group = False

        # Отримуємо відправника
        try:
            sender = await message.get_sender()
            sender_name = (
                getattr(sender, "first_name", "")
                or getattr(sender, "username", "")
                or str(message.sender_id)
            )
        except Exception:
            sender_name = str(message.sender_id)

        # Для групи — ключ по user_id, для приватного — None
        user_key = message.sender_id if is_group else None
        history = self._get_history(chat_id, user_key)

        # Додаємо повідомлення користувача в пам'ять
        self._push_message(history, ROLE_USER, text)

        # Показуємо "друкує..."
        if self.config["agent_typing_delay"]:
            async with message.client.action(chat_id, "typing"):
                try:
                    label = sender_name if (is_group and self.config["agent_show_name_in_group"]) else None
                    reply = await self._chat_with_history(history, text, sender_label=label)
                except RuntimeError as e:
                    logger.error("Mistral agent error: %s", e)
                    return
        else:
            try:
                label = sender_name if (is_group and self.config["agent_show_name_in_group"]) else None
                reply = await self._chat_with_history(history, text, sender_label=label)
            except RuntimeError as e:
                logger.error("Mistral agent error: %s", e)
                return

        # Зберігаємо відповідь у пам'яті
        self._push_message(history, ROLE_ASSISTANT, reply)

        # Надсилаємо відповідь
        await message.respond(_md_to_html(reply), parse_mode="html")

    # ════════════════════════════════════════════════════════════════════════
    # КОМАНДИ
    # ════════════════════════════════════════════════════════════════════════

    # ── Чат ───────────────────────────────────────────────────────────────

    @loader.command(ru_doc="<питання> — Запитати Mistral AI")
    async def mistral(self, message):
        """<питання> — Запитати Mistral AI"""
        if not self._check_key():
            return await utils.answer(message, self.strings["no_api_key"])
        args = utils.get_args_raw(message).strip()
        if not args:
            return await utils.answer(message, self.strings["no_args"])

        msg = await utils.answer(message, self.strings["loading"])
        try:
            text, model, elapsed = await self._chat(args)
            await utils.answer(
                msg,
                self.strings["chat_answer"].format(
                    question=args,
                    answer=_md_to_html(text),
                    model=model,
                    time=elapsed,
                ),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<модель> <питання> — Запит до конкретної моделі")
    async def mistralm(self, message):
        """<модель> <питання> — Чат із конкретною моделлю"""
        if not self._check_key():
            return await utils.answer(message, self.strings["no_api_key"])
        args = utils.get_args_raw(message).strip()
        if not args or " " not in args:
            return await utils.answer(
                message,
                "<b>❌ Формат:</b> <code>.mistralm &lt;модель&gt; &lt;питання&gt;</code>",
            )
        model, _, prompt = args.partition(" ")
        msg = await utils.answer(message, self.strings["loading"])
        try:
            text, used, elapsed = await self._chat(prompt.strip(), model=model.strip())
            await utils.answer(
                msg,
                self.strings["chat_answer"].format(
                    question=prompt.strip(),
                    answer=_md_to_html(text),
                    model=used,
                    time=elapsed,
                ),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    # ── Агент-режим ────────────────────────────────────────────────────────

    @loader.command(ru_doc="— Увімкнути/вимкнути агент-режим у поточному чаті")
    async def mistralagent(self, message):
        """— Увімкнути/вимкнути агент-режим (ШІ відповідає замість тебе)"""
        chat_id = message.chat_id
        if chat_id in self._agent_chats:
            del self._agent_chats[chat_id]
            self._save_agent_chats()
            await utils.answer(
                message,
                self.strings["agent_disabled"].format(chat=chat_id),
            )
        else:
            self._agent_chats[chat_id] = True
            self._save_agent_chats()
            await utils.answer(
                message,
                self.strings["agent_enabled"].format(chat=chat_id),
            )

    @loader.command(ru_doc="— Показати всі чати де активний агент-режим")
    async def mistralagentlist(self, message):
        """— Список чатів з активним агент-режимом"""
        if not self._agent_chats:
            return await utils.answer(message, self.strings["agent_list_empty"])
        lines = [f"• <code>{cid}</code>" for cid in self._agent_chats]
        await utils.answer(
            message,
            self.strings["agent_list_header"].format(chats="\n".join(lines)),
        )

    @loader.command(ru_doc="— Очистити пам'ять агента у поточному чаті")
    async def mistralagentclear(self, message):
        """— Очистити пам'ять агента (контекст розмови)"""
        chat_id = message.chat_id
        if chat_id in self._agent_memory:
            del self._agent_memory[chat_id]
        await utils.answer(
            message,
            self.strings["agent_memory_cleared"].format(chat=chat_id),
        )

    # ── Інструменти ────────────────────────────────────────────────────────

    @loader.command(ru_doc="— Список доступних моделей Mistral")
    async def mistralmodels(self, message):
        """— Показати всі доступні моделі"""
        if not self._check_key():
            return await utils.answer(message, self.strings["no_api_key"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            models = await self._list_models()
            if not models:
                return await utils.answer(msg, "<b>❌ Моделі не знайдено.</b>")
            lines = []
            for m in sorted(models, key=lambda x: x.get("id", "")):
                mid = m.get("id", "?")
                caps = m.get("capabilities", {})
                tags = []
                if caps.get("completion_chat"):
                    tags.append("💬")
                if caps.get("vision"):
                    tags.append("👁")
                if caps.get("function_calling"):
                    tags.append("🔧")
                if caps.get("fine_tuning"):
                    tags.append("🎯")
                lines.append(f"• <code>{mid}</code> {' '.join(tags)}")
            text = self.strings["models_header"] + "\n".join(lines)
            if len(text) > 4096:
                text = text[:4090] + "\n..."
            await utils.answer(msg, text)
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="— OCR зображення або PDF (відповідь на медіа)")
    async def mistralocr(self, message):
        """— OCR зображення/PDF. Відповідь на фото або файл."""
        if not self._check_key():
            return await utils.answer(message, self.strings["no_api_key"])
        reply = await message.get_reply_message()
        msg = await utils.answer(message, self.strings["loading"])
        try:
            if reply and reply.photo:
                photo_bytes = await reply.download_media(bytes)
                result = await self._ocr_base64(photo_bytes, "image/jpeg")
            elif reply and reply.document:
                mime = reply.document.mime_type or ""
                doc_bytes = await reply.download_media(bytes)
                mt = "application/pdf" if "pdf" in mime else "image/jpeg"
                result = await self._ocr_base64(doc_bytes, mt)
            else:
                return await utils.answer(msg, self.strings["ocr_no_media"])
            if not result:
                result = "<i>(текст не знайдено)</i>"
            output = self.strings["ocr_result"].format(text=result)
            if len(output) > 4096:
                output = output[:4090] + "\n..."
            await utils.answer(msg, output)
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<текст> — Синтез мовлення (TTS)")
    async def mistralvoice(self, message):
        """<текст> — Перетворити текст на голос (TTS)"""
        if not self._check_key():
            return await utils.answer(message, self.strings["no_api_key"])
        args = utils.get_args_raw(message).strip()
        if not args:
            return await utils.answer(message, self.strings["no_args"])
        msg = await utils.answer(message, self.strings["tts_generating"])
        try:
            wav_bytes = await self._tts(args)
            await message.client.send_file(
                message.peer_id,
                file=io.BytesIO(wav_bytes),
                attributes=[],
                voice_note=True,
                caption=self.strings["tts_done"],
                reply_to=message.reply_to_msg_id,
            )
            await msg.delete()
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="— Транскрипція аудіо/голосу (відповідь на аудіо)")
    async def mistraltranscribe(self, message):
        """— Транскрибувати голосове або аудіо повідомлення"""
        if not self._check_key():
            return await utils.answer(message, self.strings["no_api_key"])
        reply = await message.get_reply_message()
        if not reply or not (reply.voice or reply.audio or reply.document):
            return await utils.answer(message, self.strings["transcription_no_audio"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            audio_bytes = await reply.download_media(bytes)
            fname = "audio.ogg"
            if reply.audio:
                fname = "audio.mp3"
            elif reply.document and reply.document.attributes:
                fname = getattr(reply.document.attributes[0], "file_name", "audio.ogg")
            text = await self._transcribe(audio_bytes, fname)
            if not text:
                text = "<i>(текст не розпізнано)</i>"
            await utils.answer(
                msg, self.strings["transcription_result"].format(text=text)
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<текст> — Отримати ембединг тексту")
    async def mistralembed(self, message):
        """<текст> — Отримати векторне представлення тексту"""
        if not self._check_key():
            return await utils.answer(message, self.strings["no_api_key"])
        args = utils.get_args_raw(message).strip()
        if not args:
            return await utils.answer(message, self.strings["no_args"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            vec, model = await self._embeddings(args)
            preview = ", ".join(f"{v:.4f}" for v in vec[:5])
            await utils.answer(
                msg,
                self.strings["embed_result"].format(
                    model=model, dim=len(vec), preview=preview
                ),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    @loader.command(ru_doc="<текст> — Перевірити текст на порушення правил")
    async def mistralmod(self, message):
        """<текст> — Модерація тексту"""
        if not self._check_key():
            return await utils.answer(message, self.strings["no_api_key"])
        args = utils.get_args_raw(message).strip()
        if not args:
            return await utils.answer(message, self.strings["no_args"])
        msg = await utils.answer(message, self.strings["loading"])
        try:
            data = await self._moderate(args)
            results = data.get("results", [{}])[0]
            flagged = results.get("flagged", False)
            cats = results.get("categories", {})
            active = [k for k, v in cats.items() if v]
            safe_str = "✅ Так" if not flagged else "🚫 Ні (порушення)"
            cats_str = ", ".join(active) if active else "немає"
            await utils.answer(
                msg,
                self.strings["moderation_result"].format(
                    safe=safe_str, categories=cats_str
                ),
            )
        except RuntimeError as e:
            await utils.answer(msg, self.strings["error"].format(error=e))

    # ── Довідка ────────────────────────────────────────────────────────────

    @loader.command(ru_doc="— Показати допомогу по модулю")
    async def mistralhelp(self, message):
        """— Список команд модуля MistralAI"""
        await utils.answer(
            message,
            "<b>🤖 MistralAI v2 — команди:</b>\n\n"
            "<b>💬 Чат</b>\n"
            "<code>.mistral &lt;питання&gt;</code> — Чат з Mistral\n"
            "<code>.mistralm &lt;модель&gt; &lt;питання&gt;</code> — Конкретна модель\n"
            "<code>.mistralmodels</code> — Список моделей\n\n"
            "<b>🤖 Агент-режим</b>\n"
            "<code>.mistralagent</code> — Увімкнути/вимкнути у поточному чаті\n"
            "<code>.mistralagentlist</code> — Список активних агент-чатів\n"
            "<code>.mistralagentclear</code> — Очистити пам'ять агента\n\n"
            "<b>🛠 Інструменти</b>\n"
            "<code>.mistralocr</code> — OCR фото або PDF\n"
            "<code>.mistralvoice &lt;текст&gt;</code> — TTS синтез мовлення\n"
            "<code>.mistraltranscribe</code> — Транскрипція аудіо\n"
            "<code>.mistralembed &lt;текст&gt;</code> — Ембединг тексту\n"
            "<code>.mistralmod &lt;текст&gt;</code> — Модерація тексту\n\n"
            "<i>⚙️ Налаштування: <code>.config MistralAI</code></i>",
        )
