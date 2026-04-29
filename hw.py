#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/hw_icon.png
# meta banner: https://mods.hikariatama.ru/badges/hw.jpg
# meta developer: @rotkranz
# scope: hikka_only
# scope: hikka_min 1.2.10

from random import randint

from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class HomeworkMod(loader.Module):
    """Simple Homework planner"""

    strings = {
        "name": "HomeWork",
        "no_hometask": "🚫 <b>You haven't provided hometask</b>",
        "new_hometask": "<b>Hometask </b><code>#{}</code>:\n<pre>{}</pre>",
        "not_found": "<b>🚫 Hometask not found</b",
        "removed": "<b>✅ Hometask removed</b>",
    }

    strings_ru = {
        "no_hometask": "🚫 <b>Укажи домашнее задание</b>",
        "new_hometask": "<b>Домашнее задание </b><code>#{}</code>:\n<pre>{}</pre>",
        "not_found": "<b>🚫 Домашнее задание не найдено</b",
        "removed": "<b>✅ Домашнее задание удалено</b>",
        "_cmd_doc_hw": "<item> - Новое домашнее задание",
        "_cmd_doc_hwl": "Список домашних заданий",
        "_cmd_doc_uhw": "<id> - Удалить домашнее задание",
        "_cls_doc": "Простой планнер домашних заданий",
    }

    async def client_ready(self, client, db):
        self.hw = self.get("hw", {})

    async def hwcmd(self, message: Message):
        """<item> - New hometask"""

        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        if args == "" and not reply:
            await utils.answer(message, self.strings("no_hometask"))
            return

        if args == "":
            args = reply.text

        random_id = str(randint(10000, 99999))

        self.hw[random_id] = args

        self.set("hw", self.hw)
        await utils.answer(
            message,
            self.strings("new_hometask").format(random_id, str(args)),
        )

    @loader.unrestricted
    async def hwlcmd(self, message: Message):
        """List of hometasks"""
        res = "<b>#HW:</b>\n\n"

        for item_id, item in self.hw.items():
            res += f"🔸 <code>.uhw {item_id}</code>: <code>{item}" + "</code>\n"

        await utils.answer(message, res)

    async def uhwcmd(self, message: Message):
        """<id> - Remove hometask"""
        args = utils.get_args_raw(message)
        if args.startswith("#"):
            args = args[1:]

        if args not in self.hw:
            await utils.answer(message, self.strings("not_found"))
            return

        del self.hw[args]
        self.set("hw", self.hw)
        await utils.answer(message, self.strings("removed"))
