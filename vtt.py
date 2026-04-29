__version__ = (2, 0, 1)

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/vtt_icon.png
# meta banner: https://mods.hikariatama.ru/badges/vtt.jpg
# meta developer: @rotkranz
# scope: ffmpeg
# scope: hikka_only
# scope: hikka_min 1.3.3
# requires: pydub speechrecognition python-ffmpeg

import asyncio
import logging
import os
import tempfile

import speech_recognition as sr
from pydub import AudioSegment
from telethon.tl.types import DocumentAttributeVideo, Message

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class VoicyMod(loader.Module):
    """Recognize voice messages, audios, videos and round messages"""

    strings = {
        "name": "Voicy",
        "converting": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Recognizing voice"
            " message...</b>"
        ),
        "converted": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji>"
            " Recognized:</b>\n<i>{}</i>"
        ),
        "voice_not_found": (
            "<emoji document_id=6041850934756119589>🫠</emoji> <b>Voice not found</b>"
        ),
        "autovoice_off": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> I will not recognize"
            " voice messages in this chat</b>"
        ),
        "autovoice_on": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> I will recognize"
            " voice messages in this chat</b>"
        ),
        "_cfg_lang": "Language of voices to recognize",
        "_cfg_engine": "Recognition engine",
        "error": "🚫 <b>Recognition error!</b>",
        "_cfg_ignore_users": "Users to ignore",
        "_cfg_silent": "Silent mode - do not notify about errors",
        "too_big": "🫥 <b>Voice message is too big, I can't recognise it...</b>",
    }

    strings_ru = {
        "converting": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Распознаю голосовое"
            " сообщение...</b>"
        ),
        "converted": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji>"
            " Распознано:</b>\n<i>{}</i>"
        ),
        "voice_not_found": (
            "<emoji document_id=6041850934756119589>🫠</emoji> <b>Нет ответа на"
            " войс</b>"
        ),
        "autovoice_off": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Я больше не буду"
            " распознавать голосовые сообщения в этом чате</b>"
        ),
        "autovoice_on": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Я буду распознавать"
            " голосовые сообщения в этом чате</b>"
        ),
        "_cmd_doc_voicy": "Распознает голосовое сообщение",
        "_cmd_doc_autovoice": (
            "Включить\\выключить автораспознавание голосовых сообщений в чате"
        ),
        "_cls_doc": "Распознает голосовые сообщения, аудио, видео и кругляши",
        "_cfg_lang": "Язык для распознавания голосовых сообщений",
        "_cfg_engine": "Распознаватель",
        "_cfg_ignore_users": "Игнорировать пользователей",
        "_cfg_silent": "Тихий режим - не оповещать об ошибках",
        "error": "🚫 <b>Ошибка распознавания!</b>",
        "too_big": (
            "🫥 <b>Голосовое сообщение слишком большое, я не могу его распознать...</b>"
        ),
    }

    strings_de = {
        "converting": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Sprachnachricht wird"
            " erkannt...</b>"
        ),
        "converted": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji>"
            " Erkannt:</b>\n<i>{}</i>"
        ),
        "voice_not_found": (
            "<emoji document_id=6041850934756119589>🫠</emoji> <b>Keine Antwort auf"
            " Voice</b>"
        ),
        "autovoice_off": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Ich werde in diesem"
            " Chat keine Sprachnachrichten mehr erkennen</b>"
        ),
        "autovoice_on": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Ich werde in diesem"
            " Chat Sprachnachrichten erkennen</b>"
        ),
        "_cmd_doc_voicy": "Erkennt eine Sprachnachricht",
        "_cmd_doc_autovoice": (
            "Aktiviert\\Deaktiviert die automatische Erkennung von Sprachnachrichten im"
            " Chat"
        ),
        "_cls_doc": "Erkennt Sprachnachrichten, Audios, Videos und Rundnachrichten",
        "_cfg_lang": "Sprache für die Spracherkennung",
        "_cfg_engine": "Erkennungsprogramm",
        "_cfg_ignore_users": "Benutzer ignorieren",
        "_cfg_silent": "Stiller Modus - Fehler nicht melden",
        "error": "🚫 <b>Erkennungsfehler!</b>",
        "too_big": (
            "🫥 <b>Sprachnachricht ist zu groß, ich kann sie nicht erkennen...</b>"
        ),
    }

    strings_tr = {
        "converting": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Sesli mesajı"
            " tanıyorum...</b>"
        ),
        "converted": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji>"
            " Tanımlandı:</b>\n<i>{}</i>"
        ),
        "voice_not_found": (
            "<emoji document_id=6041850934756119589>🫠</emoji> <b>Sesli mesaja cevap"
            " yok</b>"
        ),
        "autovoice_off": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Bu sohbetteki sesli"
            " mesajları artık tanımayacağım</b>"
        ),
        "autovoice_on": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Bu sohbetteki sesli"
            " mesajları tanıyacağım</b>"
        ),
        "_cmd_doc_voicy": "Sesli mesajı tanır",
        "_cmd_doc_autovoice": (
            "Sohbetteki sesli mesajların otomatik tanınmasını etkinleştirir\\devre dışı"
            " bırakır"
        ),
        "_cls_doc": "Sesli mesajları, sesleri, videoları ve çevirileri tanır",
        "_cfg_lang": "Ses tanıma için dil",
        "_cfg_engine": "Tanıyıcı",
        "_cfg_ignore_users": "Kullanıcıları yoksay",
        "_cfg_silent": "Sessiz mod - hataları bildirmeyin",
        "error": "🚫 <b>Tanıma hatası!</b>",
        "too_big": "🫥 <b>Sesli mesaj çok büyük, tanıyamıyorum...</b>",
    }

    strings_uz = {
        "converting": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> So'zli xabar"
            " aniqlanmoqda...</b>"
        ),
        "converted": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji>"
            " Aniqlandi:</b>\n<i>{}</i>"
        ),
        "voice_not_found": (
            "<emoji document_id=6041850934756119589>🫠</emoji> <b>So'zli xabarga"
            " javob yo'q</b>"
        ),
        "autovoice_off": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Bu suhbatda so'zli"
            " xabarlar aniqlanmaydi</b>"
        ),
        "autovoice_on": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> Bu suhbatda so'zli"
            " xabarlar aniqlanadi</b>"
        ),
        "_cmd_doc_voicy": "So'zli xabarni aniqlash",
        "_cmd_doc_autovoice": (
            "Suhbatdagi so'zli xabarlar avtomatik aniqlashini yoqish\\o'chirish"
        ),
        "_cls_doc": "So'zli xabarlar, audio, videolar va qarishmalarni aniqlaydi",
        "_cfg_lang": "Tilni aniqlash uchun",
        "_cfg_engine": "Aniqlash moliyaviyasi",
        "_cfg_ignore_users": "Foydalanuvchilarni e'tiborsiz qoldirish",
        "_cfg_silent": "Sessiz rejim - xatolarni bildirmang",
        "error": "🚫 <b>Aniqlash xatosi!</b>",
        "too_big": "🫥 <b>So'zli xabar juda katta, aniqlay olmayman...</b>",
    }

    strings_hi = {
        "converting": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> वायस संदेश"
            " पहचान रहा है...</b>"
        ),
        "converted": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji>"
            " पहचान लिया:</b>\n<i>{}</i>"
        ),
        "voice_not_found": (
            "<emoji document_id=6041850934756119589>🫠</emoji> <b>वायस संदेश"
            " के लिए जवाब नहीं</b>"
        ),
        "autovoice_off": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> इस चैट में वायस"
            " संदेश पहचान नहीं करेंगे</b>"
        ),
        "autovoice_on": (
            "<b><emoji document_id=6041850934756119589>🫠</emoji> इस चैट में वायस"
            " संदेश पहचान करेंगे</b>"
        ),
        "_cmd_doc_voicy": "वायस संदेश पहचान करें",
        "_cmd_doc_autovoice": "इस चैट में वायस संदेशों को ऑटोमैटिक पहचानने को सक्षम\\अक्षम करें",
        "_cls_doc": "वायस संदेश, ऑडियो, वीडियो और रैडियो संदेश पहचानता है",
        "_cfg_lang": "पहचान के लिए भाषा",
        "_cfg_engine": "पहचानकर्ता",
        "_cfg_ignore_users": "उपयोगकर्ताओं को नजरअंदाज करें",
        "_cfg_silent": "शांत मोड - त्रुटियों को सूचित न करें",
        "error": "🚫 <b>पहचान त्रुटि!</b>",
        "too_big": "🫥 <b>वायस संदेश बहुत बड़ा है, पहचान नहीं कर सकता...</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "language",
                "ru-RU",
                lambda: self.strings("_cfg_lang"),
                validator=loader.validators.RegExp(r"^[a-z]{2}-[A-Z]{2}$"),
            ),
            loader.ConfigValue(
                "ignore_users",
                [],
                lambda: self.strings("_cfg_ignore_users"),
                validator=loader.validators.Series(
                    validator=loader.validators.TelegramID()
                ),
            ),
            loader.ConfigValue(
                "silent",
                False,
                lambda: self.strings("_cfg_silent"),
                validator=loader.validators.Boolean(),
            ),
        )

    async def client_ready(self):
        self.v2a = await self.import_lib(
            "https://libs.hikariatama.ru/v2a.py",
            suspend_on_error=True,
        )
        self.chats = self.pointer("chats", [])

    async def recognize(self, message: Message):
        try:
            m = await utils.answer(message, self.strings("converting"))
            with tempfile.TemporaryDirectory() as tmpdir:
                file = os.path.join(
                    tmpdir,
                    "audio.mp3" if message.audio else "audio.ogg",
                )

                data = await message.download_media(bytes)

                if message.video:
                    data = await self.v2a.convert(data, "audio.ogg")

                with open(file, "wb") as f:
                    f.write(data)

                song = AudioSegment.from_file(
                    file, format="mp3" if message.audio else "ogg"
                )
                song.export(os.path.join(tmpdir, "audio.wav"), format="wav")

                r = sr.Recognizer()

                with sr.AudioFile(os.path.join(tmpdir, "audio.wav")) as source:
                    audio_data = r.record(source)
                    text = await utils.run_sync(
                        r.recognize_google,
                        audio_data,
                        language=self.config["language"],
                    )
                    m = await utils.answer(
                        m,
                        self.strings("converted").format(text),
                    )
        except Exception:
            logger.exception("Can't recognize")
            if not self.config["silent"]:
                m = await utils.answer(m, self.strings("error"))
                await asyncio.sleep(3)
                if not message.out:
                    await m.delete()

    @loader.unrestricted
    async def voicycmd(self, message: Message):
        """Recognize voice message"""
        reply = await message.get_reply_message()
        try:
            is_voice = (
                reply.video or reply.audio or reply.media.document.attributes[0].voice
            )
        except (AttributeError, IndexError):
            is_voice = False

        if not reply or not reply.media or not is_voice:
            await utils.answer(message, self.strings("voice_not_found"))
            return

        if message.out:
            await message.delete()

        await self.recognize(reply)

        if message.out:
            await message.delete()

    async def watcher(self, message: Message):
        try:
            if (
                utils.get_chat_id(message) not in self.get("chats", [])
                or not message.media
                or not message.video
                and not message.audio
                and not message.media.document.attributes[0].voice
                or message.gif
                or message.sticker
            ):
                return
        except Exception:
            return

        if message.sender_id in self.config["ignore_users"]:
            return

        if (
            (
                message.video
                and (
                    next(
                        attr
                        for attr in message.video.attributes
                        if isinstance(attr, DocumentAttributeVideo)
                    ).duration
                    > 120
                )
            )
            or getattr(
                (
                    getattr(
                        getattr(getattr(message, "media", None), "document", None),
                        "attributes",
                        False,
                    )
                    or [None]
                )[0],
                "duration",
                0,
            )
            > 300
            or message.document.size / 1024 / 1024 > 5
        ):
            if not self.config["silent"]:
                await utils.answer(message, self.strings("too_big"))
            return

        await self.recognize(message)

    async def autovoicecmd(self, message: Message):
        """Toggle automatic recognition in current chat"""
        chat_id = utils.get_chat_id(message)

        if chat_id in self.get("chats", []):
            self.chats.remove(chat_id)
            await utils.answer(message, self.strings("autovoice_off"))
        else:
            self.chats.append(chat_id)
            await utils.answer(message, self.strings("autovoice_on"))
