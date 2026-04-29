#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://img.icons8.com/fluency/240/000000/apple-music-lyrics.png
# meta banner: https://mods.hikariatama.ru/badges/dyslexia.jpg
# meta developer: @rotkranz
# scope: inline
# scope: hikka_only
# scope: hikka_min 1.2.10

import re
from random import shuffle

from telethon.tl.types import Message

from .. import loader, utils


def dyslex(text: str) -> str:
    res = ""
    for word in text.split():
        newline = False
        if "\n" in word:
            word = word.replace("\n", "")
            newline = True

        to_shuffle = re.sub(r"[^a-zA-Zа-яА-Я0-9]", "", word)[1:-1]
        shuffled = list(to_shuffle)
        shuffle(shuffled)

        res += word.replace(to_shuffle, "".join(shuffled)) + " "
        if newline:
            res += "\n"

    return res


@loader.tds
class DyslexiaMod(loader.Module):
    """Shows the text as how you would see it if you have dyslexia"""

    strings = {
        "name": "Dyslexia",
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>You need to provide"
            " text</b>"
        ),
    }
    strings_ru = {
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Текст не найден</b>"
        ),
        "_cmd_doc_dyslex": (
            "<текст | реплай> - Показывает, как люди с дислексией бы видели этот текст"
        ),
    }
    strings_de = {
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Kein Text"
            " gefunden</b>"
        ),
        "_cmd_doc_dyslex": (
            "<text | reply> - Zeigt den Text so an, wie er für Menschen mit Dyslexie"
            " aussieht"
        ),
    }
    strings_hi = {
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>पाठ नहीं मिला</b>"
        ),
        "_cmd_doc_dyslex": "<पाठ | रिप्लाई> - डिस्लेक्सिया वाले लोगों के लिए यह पाठ दिखाता है",
    }
    strings_uz = {
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Matn topilmadi</b>"
        ),
        "_cmd_doc_dyslex": (
            "<matn | javob> - Dyslexia bo'lgan odamlar uchun ushbu matnni ko'rsatadi"
        ),
    }
    strings_tr = {
        "no_text": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Metin bulunamadı</b>"
        ),
        "_cmd_doc_dyslex": (
            "<metin | yanıt> - Dyslexia olan insanlar için bu metni gösterir"
        ),
    }

    async def dyslexcmd(self, message: Message):
        """<text | reply> - Show, how people with dyslexia would have seen this text"""
        args = utils.get_args_raw(message)
        if not args:
            try:
                args = (await message.get_reply_message()).text
            except Exception:
                return await utils.answer(message, self.strings("no_text"))

        await self.animate(
            message,
            [dyslex(args) for _ in range(20)],
            interval=2,
            inline=True,
        )
