#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/cloud_icon.png
# meta banner: https://mods.hikariatama.ru/badges/cloud.jpg
# meta developer: @rotkranz
# scope: hikka_only
# scope: hikka_min 1.2.10

import time

import requests
from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class ModuleCloudMod(loader.Module):
    """Hikari modules management"""

    strings = {
        "name": "ModuleCloud",
        "args": "🚫 <b>Args not specified</b>",
        "mod404": "🚫 <b>Module {} not found</b>",
        "ilink": (
            "<emoji document_id=5370705803051279512>🐹</emoji> <b><u>{name}</u> - <a"
            ' href="https://mods.hikariatama.ru/view/{file}.py">source</a></b>\n<emoji'
            " document_id=5787544344906959608>ℹ️</emoji> <i>{desc}</i>\n\n<i>By"
            " @rotkranz with </i><emoji"
            " document_id=5875452644599795072>🔞</emoji>\n\n<emoji"
            " document_id=5188377234380954537>🌘</emoji> <code>.dlm {file}</code>"
        ),
        "404": "😔 <b>Module not found</b>",
        "not_exact": (
            "⚠️ <b>No exact match occured, so the closest result is shown instead</b>"
        ),
    }

    @loader.unrestricted
    async def ilinkcmd(self, message: Message):
        """<modname> - Get hikari module banner"""
        args = utils.get_args_raw(message)

        badge = await utils.run_sync(
            requests.get,
            f"https://mods.hikariatama.ru/badge/{args}",
        )

        if badge.status_code == 404:
            await utils.answer(message, self.strings("mod404").format(args))
            return

        img = requests.get(badge.json()["badge"] + f"?t={round(time.time())}").content
        info = badge.json()["info"]
        info["file"] = info["file"].split(".")[0]

        if not message.media or not message.out:
            await self._client.send_file(
                message.peer_id,
                img,
                caption=self.strings("ilink").format(**info),
            )
            await message.delete()
        else:
            await message.edit(self.strings("ilink").format(**info), file=img)
