#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# scope: hikka_min 1.2.10

# meta pic: https://img.icons8.com/fluency/240/000000/archive.png
# meta banner: https://mods.hikariatama.ru/badges/web2file.jpg
# meta developer: @rotkranz

import io

import requests
from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class Web2fileMod(loader.Module):
    """Download content from link and send it as file"""

    strings = {
        "name": "Web2file",
        "no_args": "🚫 <b>Specify link</b>",
        "fetch_error": "🚫 <b>Download error</b>",
        "loading": "🦊 <b>Downloading...</b>",
    }

    strings_ru = {
        "no_args": "🚫 <b>Укажи ссылку</b>",
        "fetch_error": "🚫 <b>Ошибка загрузки</b>",
        "loading": "🦊 <b>Загрузка...</b>",
        "_cls_doc": "Скачивает содержимое ссылки и отправляет в виде файла",
    }

    async def web2filecmd(self, message: Message):
        """Send link content as file"""
        website = utils.get_args_raw(message)
        if not website:
            await utils.answer(message, self.strings("no_args", message))
            return
        try:
            f = io.BytesIO(requests.get(website).content)
        except Exception:
            await utils.answer(message, self.strings("fetch_error", message))
            return

        f.name = website.split("/")[-1]

        await message.respond(file=f)
        await message.delete()
