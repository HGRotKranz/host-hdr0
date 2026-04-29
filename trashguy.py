#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/trashguy_icon.png
# meta banner: https://mods.hikariatama.ru/badges/trashguy.jpg
# meta developer: @rotkranz
# scope: inline
# scope: hikka_only
# scope: hikka_min 1.2.10

import grapheme
from telethon.tl.types import Message

from .. import loader, utils


def trashguy(text: str) -> list:
    DISTANCE = 5
    SPACER = "\u0020\u2800"
    text = list(grapheme.graphemes(text))
    return [
        utils.escape_html(i)
        for i in utils.array_sum(
            [
                [
                    f"🗑{SPACER * i}(>"
                    f" ^_^)>{SPACER * (DISTANCE - i)}{''.join(text[offset:])}"
                    for i in range(DISTANCE)
                ]
                + [
                    f"🗑{SPACER * (DISTANCE - i)}{current_symbol}<(^_^"
                    f" <){SPACER * i}{''.join(text[offset + 1:])}"
                    for i in range(DISTANCE)
                ]
                for offset, current_symbol in enumerate(text)
            ]
        )
    ]


@loader.tds
class TrashGuyMod(loader.Module):
    """Animation of trashguy taking out the trash"""

    strings = {
        "name": "TrashGuy",
        "done": (
            "🗑 \\ (•◡•) /"
            " 🗑\n\u0020\u2800\u0020\u2800<b>Done!</b>\u0020\u2800\u0020\u2800"
        ),
    }

    strings_ru = {
        "done": (
            "🗑 \\ (•◡•) / 🗑\n\u0020\u2800\u0020\u2800<b>Я"
            " закончил!</b>\u0020\u2800\u0020\u2800"
        ),
    }

    async def tguyicmd(self, message: Message):
        """<text> - TrashGuy Inline"""
        await self.animate(
            message,
            trashguy(utils.get_args_raw(message) or "hikari's brain")
            + [self.strings("done")],
            interval=1,
            inline=True,
        )

    async def tguycmd(self, message: Message):
        """<text> - TrashGuy"""
        await self.animate(
            message,
            trashguy(utils.get_args_raw(message) or "hikari's brain")
            + [self.strings("done")],
            interval=1,
        )
