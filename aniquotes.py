#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/aniquotes_icon.png
# meta banner: https://mods.hikariatama.ru/badges/aniquotes.jpg
# meta developer: @rotkranz
# scope: hikka_only
# scope: hikka_min 1.2.10

from random import choice

from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class AnimatedQuotesMod(loader.Module):
    """Simple module to create animated stickers via bot"""

    strings = {
        "name": "AnimatedQuotes",
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Provide a text to"
            " create sticker with</b>"
        ),
        "processing": (
            "<emoji document_id=5451646226975955576>⌛️</emoji> <b>Processing...</b>"
        ),
    }

    strings_ru = {
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Укажи текст для"
            " создания стикера</b>"
        ),
        "processing": (
            "<emoji document_id=5451646226975955576>⌛️</emoji> <b>Обработка...</b>"
        ),
        "_cmd_doc_aniq": "<text> - Создать анимированный стикер",
        "_cls_doc": "Простенький модуль, который создает анимированные стикеры",
    }

    strings_de = {
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bitte gib einen Text"
            " an, um einen Sticker zu erstellen</b>"
        ),
        "processing": (
            "<emoji document_id=5451646226975955576>⌛️</emoji> <b>Verarbeitung...</b>"
        ),
        "_cmd_doc_aniq": "<text> - Erstelle einen animierten Sticker",
        "_cls_doc": "Einfaches Modul, das animierte Sticker erstellt",
    }

    strings_hi = {
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>एक टेक्स्ट दें जिसके"
            " लिए एक स्टिकर बनाना है</b>"
        ),
        "processing": (
            "<emoji document_id=5451646226975955576>⌛️</emoji> <b>प्रोसेसिंग...</b>"
        ),
        "_cmd_doc_aniq": "<text> - एक एनीमेटेड स्टिकर बनाएं",
        "_cls_doc": "एक एनीमेटेड स्टिकर बनाने के लिए एक सरल मॉड्यूल",
    }

    strings_uz = {
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Sticker yaratish"
            " uchun"
            " matn kiriting</b>"
        ),
        "processing": (
            "<emoji document_id=5451646226975955576>⌛️</emoji> <b>Islenmoqda...</b>"
        ),
        "_cmd_doc_aniq": "<matn> - Animatsiya stikerni yaratish",
        "_cls_doc": "Animatsiya stikerni yaratish uchun oddiy modul",
    }

    strings_tr = {
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bir metin girin</b>"
        ),
        "processing": (
            "<emoji document_id=5451646226975955576>⌛️</emoji> <b>İşleniyor...</b>"
        ),
        "_cmd_doc_aniq": "<text> - Animasyonlu alıntı oluştur",
        "_cls_doc": "Animasyonlu stiker oluşturmak için basit bir modül",
    }

    async def aniqcmd(self, message: Message):
        """<text> - Create animated quote"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_text"))
            return

        message = await utils.answer(message, self.strings("processing"))

        try:
            query = await self._client.inline_query("@QuotAfBot", args)
            await message.respond(file=choice(query).document)
        except Exception as e:
            await utils.answer(message, str(e))
            return

        if message.out:
            await message.delete()
