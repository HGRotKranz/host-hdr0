#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/forbid_joins_icon.png
# meta banner: https://mods.hikariatama.ru/badges/forbid_joins.jpg
# meta developer: @rotkranz
# scope: hikka_only
# scope: hikka_min 1.2.10

from .. import loader


@loader.tds
class ForbidJoinMod(loader.Module):
    """Tired of trojans in modules, which join channels? Load this module!"""

    strings = {
        "name": "ForbidJoin",
        "welcome": (
            "⚔️ <b>Unit «LAMBDA» will protect you from pesky"
            " </b><code>JoinChannelRequest</code>\n\n<b>All you need is to keep this"
            " module installed!</b>\n\n<i>If any developer tries to bypass this"
            " protection, he will be added to SCAM modules list.</i>\n\n⚠️"
            " <b>Protection will be activated after you restart userbot!</b>"
        ),
    }

    strings_ru = {
        "welcome": (
            "⚔️ <b>Юнит «LAMBDA» будет защищать тебя от надоедливых"
            " </b><code>JoinChannelRequest</code>\n\n<b>Все, что требуется - держать"
            " этот модуль установленным!</b>\n\n<i>Если какой-либо разработчик"
            " попытается обойти эту защиту, он будет добавлен в список SCAM"
            " модулей.</i>\n\n⚠️ <b>Защита станет активной только после"
            " перезагрузки!</b>"
        ),
    }

    async def on_dlmod(self, client, db):
        await self.inline.bot.send_photo(
            client._tg_id,
            "https://github.com/hikariatama/assets/raw/master/unit_lambda.png",
            caption=self.strings("welcome"),
        )


# ⚠️⚠️  WARNING!  ⚠️⚠️
# If you are a module developer, and you'll try to bypass this protection to
# force user join your channel, you will be added to SCAM modules
# list and you will be banned from Hikka federation.
# Let USER decide, which channel he will follow. Do not be so petty
# I hope, you understood me.
# Thank you
