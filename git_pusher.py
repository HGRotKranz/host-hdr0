#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/git_pusher.png
# meta banner: https://mods.hikariatama.ru/badges/git_pusher.jpg
# meta developer: @rotkranz
# scope: hikka_only
# scope: hikka_min 1.2.10

import os
from random import choice

import requests
from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class GitPusherMod(loader.Module):
    """Easily push your repo from within the Telegram"""

    strings = {
        "name": "GitPusher",
        "bad_dir": "🚫 <b>Invalid directory</b>",
        "no_dir": "🚫 <b>Specify directory with </b><code>.setghdir</code>",
        "dir_set": "🌳 <b>Updated git directory to</b> <code>{}</code>",
        "terminal_required": "🚫 <b>Terminal module is required</b>",
    }

    strings_ru = {
        "bad_dir": "🚫 <b>Неверная директория</b>",
        "no_dir": "🚫 <b>Укажи директорию используя </b><code>.setghdir</code>",
        "dir_set": "🌳 <b>Директория обновлена на</b> <code>{}</code>",
        "terminal_required": "🚫 <b>Необходими модуль Terminal</b>",
        "_cmd_doc_setghdir": "<path> - Установить директорию в качестве основной",
        "_cmd_doc_push": "[commit message] - Закоммитить установленную директорию",
        "_cls_doc": "Быстро коммить изменения в директории не выходя из Телеграм",
    }

    async def client_ready(self):
        self.commits = (
            await utils.run_sync(
                requests.get,
                "https://gist.github.com/hikariatama/b0a7001306ebcc74535992c13cd33f99/raw/7a5e2c0439d31c4fedf2530ffae650ae1cb9dd0c/commit_msgs.json",
            )
        ).json()

    async def setghdircmd(self, message: Message):
        """<path> - Set directory as upstream"""
        args = utils.get_args_raw(message)
        if not args or not os.path.isdir(args.strip()):
            await utils.answer(message, self.strings("bad_dir"))
            return

        self.set("dir", args)
        await utils.answer(message, self.strings("dir_set").format(args))

    async def pushcmd(self, message: Message):
        """[commit message] - Push current upstream directory"""
        if not self.get("dir"):
            await utils.answer(message, self.strings("no_dir"))
            return

        if "terminal" not in self.allmodules.commands:
            await utils.answer(message, self.strings("terminal_required"))
            return

        args = (utils.get_args_raw(message) or choice(self.commits)).replace('"', '\\"')

        message = await utils.answer(
            message,
            (
                f"<code>.terminal cd {utils.escape_html(self.get('dir'))} && git commit"
                f' -am "{utils.escape_html(args)}" && git push</code>'
            ),
        )

        await self.allmodules.commands["terminal"](message)
