#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/neko_icon.png
# meta banner: https://mods.hikariatama.ru/badges/neko.jpg
# meta developer: @rotkranz
# scope: hikka_only
# scope: hikka_min 1.2.10

import asyncio
import functools
import json
import random
from urllib.parse import quote_plus

import requests
from telethon.tl.types import Message

from .. import loader, utils

phrases = ["Uwu", "Senpai", "Uff", "Meow", "Bonk", "Ara-ara", "Hewwo", "You're cute!"]


async def photo(self, args: str) -> str:
    return (
        await utils.run_sync(requests.get, f"{self.endpoints['img']}{args}")
    ).json()["url"]


@loader.tds
class NekosLifeMod(loader.Module):
    """NekosLife API Wrapper"""

    strings = {"name": "NekosLife"}

    strings_ru = {
        "_cmd_doc_nk": "Отправить аниме арт",
        "_cmd_doc_nkct": "Показать доступные категории",
        "_cmd_doc_owoify": "OwOфицировать текст",
        "_cmd_doc_why": "Почему?",
        "_cmd_doc_fact": "А ты знал?",
        "_cmd_doc_meow": "Отправляет ASCII-арт кошки",
        "_cls_doc": "Обертка NekosLife API",
    }

    async def client_ready(self, client, db):
        ans = (
            await utils.run_sync(requests.get, "https://nekos.life/api/v2/endpoints")
        ).json()
        self.categories = json.loads(
            "["
            + [_ for _ in ans if "/api" in _ and "/img/" in _][0]
            .split("<")[1]
            .split(">")[0]
            .replace("'", '"')
            + "]"
        )
        self.endpoints = {
            "img": "https://nekos.life/api/v2/img/",
            "owoify": "https://nekos.life/api/v2/owoify?text=",
            "why": "https://nekos.life/api/v2/why",
            "cat": "https://nekos.life/api/v2/cat",
            "fact": "https://nekos.life/api/v2/fact",
        }

    @loader.pm
    async def nkcmd(self, message: Message):
        """Send anime pic"""
        args = utils.get_args_raw(message)
        args = "neko" if args not in self.categories else args
        pic = functools.partial(photo, self=self, args=args)
        await self.inline.gallery(
            message=message,
            next_handler=pic,
            caption=lambda: f"<i>{random.choice(phrases)}</i> {utils.ascii_face()}",
        )

    @loader.pm
    async def nkctcmd(self, message: Message):
        """Show available categories"""
        cats = "\n".join(
            [" | </code><code>".join(_) for _ in utils.chunks(self.categories, 5)]
        )
        await utils.answer(
            message,
            f"<b>Available categories:</b>\n<code>{cats}</code>",
        )

    @loader.unrestricted
    async def owoifycmd(self, message: Message):
        """OwOify text"""
        args = utils.get_args_raw(message)
        if not args:
            args = await message.get_reply_message()
            if not args:
                await message.delete()
                return

            args = args.text

        if len(args) > 180:
            message = await utils.answer(message, "<b>OwOifying...</b>")

        args = quote_plus(args)
        owo = ""
        for chunk in utils.chunks(args, 180):
            owo += (
                await utils.run_sync(requests.get, f"{self.endpoints['owoify']}{chunk}")
            ).json()["owo"]
            await asyncio.sleep(0.1)
        await utils.answer(message, owo)

    @loader.unrestricted
    async def whycmd(self, message: Message):
        """Why?"""
        await utils.answer(
            message,
            (
                "<code>👾"
                f" {(await utils.run_sync(requests.get, self.endpoints['why'])).json()['why']}</code>"
            ),
        )

    @loader.unrestricted
    async def factcmd(self, message: Message):
        """Did you know?"""
        await utils.answer(
            message,
            (
                "<b>🧐 Did you know, that"
                f" </b><code>{(await utils.run_sync(requests.get, self.endpoints['fact'])).json()['fact']}</code>"
            ),
        )

    @loader.unrestricted
    async def meowcmd(self, message: Message):
        """Sends cat ascii art"""
        await utils.answer(
            message,
            (
                f"<b>{(await utils.run_sync(requests.get, self.endpoints['cat'])).json()['cat']}</b>"
            ),
        )
