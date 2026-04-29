#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# scope: hikka_min 1.2.10

# meta pic: https://img.icons8.com/color/480/000000/comedy.png
# meta banner: https://mods.hikariatama.ru/badges/rpmod.jpg
# meta developer: @rotkranz

import io
import json

import grapheme
from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, utils


@loader.tds
class RPMod(loader.Module):
    """RPMod by HikariMods"""

    strings = {
        "name": "RPMod",
        "args": "🚫 <b>Incorrect args</b>",
        "success": "✅ <b>Success</b>",
        "rp_on": "✅ <b>RPM on</b>",
        "rp_off": "✅ <b>RPM off</b>",
        "rplist": "🦊 <b>Current RP commands</b>\n\n{}",
        "backup_caption": (
            "🦊 <b>My RP commands. Restore with </b><code>.rprestore</code>"
        ),
        "no_file": "🚫 <b>Reply to file</b>",
        "restored": (
            "✅ <b>RP Commands restored. See them with </b><code>.rplist</code>"
        ),
    }

    strings_ru = {
        "args": "🚫 <b>Неверные аргументы</b>",
        "success": "✅ <b>Успешно</b>",
        "rp_on": "✅ <b>RPM включен</b>",
        "rp_off": "✅ <b>RPM выключен</b>",
        "rplist": "🦊 <b>Текущие RP команды</b>\n\n{}",
        "backup_caption": (
            "🦊 <b>Мои RP команды. Ты можешь восстановить их используя"
            " </b><code>.rprestore</code>"
        ),
        "no_file": "🚫 <b>Ответь на файл</b>",
        "restored": (
            "✅ <b>RP команды восстановлены. Их можно посмотреть используя"
            " </b><code>.rplist</code>"
        ),
        "_cmd_doc_rp": (
            "<command> <message> - Добавить RP команду. Если не указано сообщение,"
            " команда будет удалена"
        ),
        "_cmd_doc_rptoggle": "Включить\\выключить RP режим в текущем чате",
        "_cmd_doc_rplist": "Показать RP команды",
        "_cmd_doc_rpbackup": "Сохранить RP команды в файл",
        "_cmd_doc_rprestore": "Восстановить RP команды из файла",
        "_cmd_doc_rpchats": "Показать чаты, где активен режим RP",
        "_cls_doc": "RPMod от HikariMods",
    }

    async def client_ready(self, client, db):
        self.rp = self.get(
            "rp",
            {
                "поцеловать": " 💋 поцеловал",
                "чмок": " ❤️ чмокнул",
                "обнять": "☺️ обнял",
                "лизнуть": "👅 лизнул",
                "напоить": "🥃 напоил",
                "связать": "⛓ связал",
                "приковать": "🔗 приковал",
                "трахнуть": "👉👌 сочно трахнул",
                "убить": "🔪 убил",
                "уничтожить": " 💥 низвёл до атомов",
                "расстрелять": "🔫 расстрелял",
                "отдаться": "🥵 страстно отдался",
                "раб": "⛓ забрал в рабство",
            },
        )
        self.chats = self.get("active", [])

    async def rpcmd(self, message: Message):
        """<command> <message> - Add RP Command. If message unspecified, remove command"""
        args = utils.get_args_raw(message)
        try:
            command = args.split(" ", 1)[0]
            msg = args.split(" ", 1)[1]
        except Exception:
            if not args or command not in self.rp:
                await utils.answer(message, self.strings("args"))
            else:
                del self.rp[command]
                self.set("rp", self.rp)
                await utils.answer(message, self.strings("success"))

            return

        self.rp[command] = msg
        self.set("rp", self.rp)
        await utils.answer(message, self.strings("success"))

    async def rptogglecmd(self, message: Message):
        """Toggle RP Mode in current chat"""
        cid = str(utils.get_chat_id(message))
        if cid in self.chats:
            self.chats.remove(cid)
            await utils.answer(message, self.strings("rp_off"))
        else:
            self.chats += [cid]
            await utils.answer(message, self.strings("rp_on"))

        self.set("active", self.chats)

    @loader.unrestricted
    async def rplistcmd(self, message: Message):
        """List RP Commands"""
        await utils.answer(
            message,
            self.strings("rplist").format(
                "\n".join(
                    [f"    ▫️ {command} - {msg}" for command, msg in self.rp.items()]
                )
            ),
        )

    async def rpbackupcmd(self, message: Message):
        """Backup RP Commands to file"""
        file = io.BytesIO(json.dumps(self.rp).encode("utf-8"))
        file.name = "rp-backup.json"
        await self._client.send_file(
            utils.get_chat_id(message),
            file,
            caption=self.strings("backup_caption"),
        )
        await message.delete()

    async def rprestorecmd(self, message: Message):
        """Restore RP Commands from file"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(message, self.strings("no_file"))
            return

        file = (await self._client.download_file(reply.media, bytes)).decode("utf-8")

        self.rp = json.loads(file)
        self.set("rp", self.rp)
        await utils.answer(message, self.strings("restored"))

    async def rpchatscmd(self, message: Message):
        """List chats, where RPM is active"""
        await utils.answer(
            message,
            f"🦊 <b>RPM is active in {len(self.chats)} chats:</b>\n\n"
            + "\n".join(
                [
                    "    🇯🇵"
                    f" {utils.escape_html(get_display_name(await self._client.get_entity(int(chat))))}"
                    for chat in self.chats
                ]
            ),
        )

    async def watcher(self, message: Message):
        cid = str(utils.get_chat_id(message))
        try:
            if (
                cid not in self.chats
                or not isinstance(message, Message)
                or not hasattr(message, "raw_text")
                or message.raw_text.split(maxsplit=1)[0].lower() not in self.rp
            ):
                return
        except IndexError:
            return

        try:
            cmd = message.raw_text.split(maxsplit=1)[0].lower()
        except IndexError:
            return

        msg = self.rp[cmd]

        entity = None

        try:
            entity = await self._client.get_entity(
                message.raw_text.split(maxsplit=2)[1]
            )
        except Exception:
            pass

        reply = await message.get_reply_message()

        try:
            reply = await self._client.get_entity(reply.sender_id)
        except Exception:
            pass

        if not reply and not entity:
            return

        if reply and entity or not reply:
            reply = entity

        sender = await self._client.get_entity(message.sender_id)

        if utils.emoji_pattern.match(next(grapheme.graphemes(msg))):
            msg = list(grapheme.graphemes(msg))
            emoji = msg[0]
            msg = "".join(msg[1:])
        else:
            emoji = "🦊"

        await utils.answer(
            message,
            (
                f"{emoji} <a"
                f' href="tg://user?id={sender.id}">{utils.escape_html(sender.first_name)}</a>'
                f" <b>{utils.escape_html(msg)}</b> <a"
                f' href="tg://user?id={reply.id}">{utils.escape_html(reply.first_name)}</a>'
            ),
        )
