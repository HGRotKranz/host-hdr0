#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://img.icons8.com/external-wanicon-flat-wanicon/344/external-dead-halloween-costume-avatar-wanicon-flat-wanicon.png
# meta developer: @rotkranz
# meta banner: https://mods.hikariatama.ru/badges/inactive.jpg
# scope: hikka_only
# scope: hikka_min 1.3.0

import asyncio
import contextlib
import logging
import time

from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class Inactive(loader.Module):
    """Blocks people who are inactive for a long time. Check .config"""

    strings = {
        "name": "Inactive",
        "config": (
            "<emoji document_id='6041914500272098262'>🚫</emoji> <b>You need to"
            " configure module first: </b>\n\n<emoji"
            " document_id='6039769000898988691'>⚙️</emoji> <code>{}config {}</code>"
        ),
        "confirm": (
            "⚠️ <b>Please, confirm that you want to start cleaning this chat from"
            " inactive users with these parameters:</b>\n\n⌚️ <b>Inactive time:"
            " {}</b>\n💭 <b>Minimal amount of messages: {}</b>\n\n☝️ <i>Please, note,"
            " that this operation might take a lot of API requests and cause"
            " FloodWaits</i>"
        ),
        "start": "🧹 Start",
        "cancel": "🔻 Cancel",
        "configure": "⚙️ Open config",
        "started": "😼 <b>Processing started! This message will update</b>",
        "processing": (
            "🫶 <b>Processed {} messages from {} users. Already found {} users to"
            " {} and"
            " {} trusted</b>\n\n<i>Still processing...</i>"
        ),
        "kick": "kick",
        "ban": "ban",
        "processing_complete": (
            "😻 <b>Processing complete! Processed {} messages from {} users. Found {}"
            " users to {}. Apply restrictions?</b>\n"
        ),
        "processing_already": "😼 <b>Processing already in progress!</b>",
        "restrictions_applied": "🔒 <b>Action `{}` applied to {} inactive users!</b>",
        "cancelling_processing": "🔻 <b>Cancelling processing...</b>",
        "processing_cancelled": "😼 <b>Processing cancelled!</b>",
        "hrs": "hour(-s)",
        "applying_restrictions": (
            "🔒 <b>Applying restrictions. Found {} users to {}</b>"
        ),
        "restrict": "🔒 Restrict",
        "no_users": "😼 <b>No inactive users found!</b>",
        "messages": "messages",
        "waiting_lock": (
            "🛃 <b>Processing is already active in other chat, waiting for lock to"
            " release</b>"
        ),
    }

    strings_ru = {
        "config": (
            "<emoji document_id='6041914500272098262'>🚫</emoji> <b>Вам нужно вначале"
            " настроить модуль: </b>\n\n<emoji"
            " document_id='6039769000898988691'>⚙️</emoji> <code>{}config {}</code>"
        ),
        "confirm": (
            "⚠️ <b>Пожалуйста, подтвердите, что вы хотите начать очистку этого чата от"
            " неактивных пользователей с этими параметрами:</b>\n\n⌚️ <b>Время"
            " неактивности: {}</b>\n💭 <b>Минимальное количество сообщений: {}</b>\n\n☝️"
            " <i>Пожалуйста, обратите внимание, что эта операция может занять много API"
            " запросов и вызвать FloodWait'ы</i>"
        ),
        "start": "🧹 Начать",
        "cancel": "🔻 Отмена",
        "configure": "⚙️ Открыть настройки",
        "started": "😼 <b>Обработка началась! Это сообщение будет обновляться</b>",
        "processing": (
            "🫶 <b>Обработано {} сообщений от {} пользователей. Уже найдено {}"
            " пользователей для {} и {} доверенных</b>\n\n<i>Все еще обрабатываю...</i>"
        ),
        "kick": "кика",
        "ban": "бана",
        "processing_complete": (
            "😻 <b>Обработка завершена! Обработано {} сообщений от {} пользователей."
            " Найдено {} пользователей для {}. Применять ограничения?</b>\n"
        ),
        "processing_already": "😼 <b>Обработка уже выполняется!</b>",
        "restrictions_applied": (
            "🔒 <b>Действие `{}` применено к {} неактивным пользователям!</b>"
        ),
        "cancelling_processing": "🔻 <b>Отменяю обработку...</b>",
        "processing_cancelled": "😼 <b>Обработка отменена!</b>",
        "hrs": "час(-ов)",
        "applying_restrictions": (
            "🔒 <b>Применяю ограничения. Найдено {} пользователей для {}</b>"
        ),
        "restrict": "🔒 Ограничить",
        "no_users": "😼 <b>Не найдено неактивных пользователей!</b>",
        "messages": "сообщений",
        "waiting_lock": (
            "🛃 <b>Обработка уже выполняется в другом чате, жду освобождения"
            " блокировки</b>"
        ),
    }

    _lock = {}
    _global_lock = asyncio.Lock()

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "action",
                "kick",
                "Action to perform when user is inactive",
                validator=loader.validators.Choice(["ban", "kick"]),
            ),
            loader.ConfigValue(
                "inactive_time",
                None,
                (
                    "If specified, any user, which sent no messages for this amount of"
                    " hours, will be blocked."
                ),
                validator=loader.validators.Union(
                    loader.validators.Integer(minimum=1), loader.validators.NoneType()
                ),
            ),
            loader.ConfigValue(
                "inactive_messages",
                None,
                (
                    "If specified, any user, which sent less than this amount of"
                    " messages, will be blocked."
                ),
                validator=loader.validators.Union(
                    loader.validators.Integer(minimum=1), loader.validators.NoneType()
                ),
            ),
        )

    async def _configure(self, call: InlineCall):
        await self.lookup("HikkaConfig").inline__configure(
            call,
            self.__class__.__name__,
            obj_type=False,
        )

    async def _cancel(self, call: InlineCall, chat_id: int):
        if chat_id in self._lock:
            self._lock[chat_id].set()
            await call.edit(self.strings("processing_cancelled"))

    async def _start(self, call: InlineCall, chat_id: int):
        if chat_id in self._lock:
            await call.edit(self.strings("processing_already"))
            return

        self._lock[chat_id] = asyncio.Event()

        markup = {
            "text": self.strings("cancel"),
            "callback": self._cancel,
            "args": (chat_id,),
        }

        chat = await self._client.get_entity(chat_id)
        data = {}
        restrict = set()
        processing_finished = asyncio.Event()

        async def _():
            nonlocal call, data, restrict
            while True:
                await asyncio.sleep(20)
                if (
                    processing_finished.is_set()
                    or chat_id not in self._lock
                    or self._lock[chat_id].is_set()
                ):
                    break

                await call.edit(
                    self.strings("processing").format(
                        sum([len(user_messages) for user_messages in data.values()]),
                        len(data),
                        len(restrict),
                        self.strings(self.config["action"]),
                        len(
                            [
                                user
                                for user, messages in data.items()
                                if (
                                    not self.config["inactive_messages"]
                                    or len(messages) > self.config["inactive_messages"]
                                )
                                and (
                                    not self.config["inactive_time"]
                                    or messages
                                    and time.time() - max(messages)
                                    < self.config["inactive_time"] * 3600
                                )
                            ]
                        ),
                    ),
                    reply_markup=markup,
                )

        await call.edit(
            (
                self.strings("waiting_lock")
                if self._global_lock.locked()
                else self.strings("started")
            ),
            reply_markup=markup,
        )

        async with self._global_lock:
            if self._lock[chat_id].is_set():
                await call.edit(self.strings("processing_cancelled"))
                self._lock.pop(chat_id)
                return

            task = asyncio.ensure_future(_())

            names = {}

            with contextlib.suppress(Exception):
                await self._client.end_takeout(True)

            async with self._client.takeout(
                **({"megagroups": True} if chat.megagroup else {"chats": True})
            ) as takeout:
                async for user in takeout.iter_participants(chat):
                    data.setdefault(user.id, [])
                    names[user.id] = get_display_name(user)

                async for message in takeout.iter_messages(chat, wait_time=5):
                    sender = message.sender_id
                    if sender not in names:
                        continue

                    date = time.mktime(message.date.timetuple())
                    data.setdefault(sender, []).append(date)
                    if self.config["inactive_time"]:
                        if (
                            time.time() - max(data[sender])
                            > self.config["inactive_time"] * 3600
                        ):
                            restrict.add(sender)
                        elif sender in restrict:
                            restrict.remove(sender)

                    if self.config["inactive_messages"]:
                        if len(data[sender]) < self.config["inactive_messages"]:
                            restrict.add(sender)
                        elif sender in restrict:
                            restrict.remove(sender)

                    if (
                        self.config["inactive_messages"]
                        and all(
                            len(msgs) > self.config["inactive_messages"]
                            for msgs in data.values()
                        )
                        and (
                            not self.config["inactive_time"]
                            or all(
                                msgs
                                and time.time() - max(msgs)
                                > self.config["inactive_time"] * 3600
                                for msgs in data.values()
                            )
                        )
                    ):
                        break

                    if self._lock[chat_id].is_set():
                        await call.edit(self.strings("processing_cancelled"))
                        self._lock.pop(chat_id)
                        return

        for user, messages in data.items():
            if (
                self.config["inactive_messages"]
                and len(messages) < self.config["inactive_messages"]
                or self.config["inactive_time"]
                and time.time() - max(messages) > self.config["inactive_time"] * 3600
            ):
                restrict.add(user)
            elif user in restrict:
                restrict.remove(user)

        processing_finished.set()
        task.cancel()

        if not restrict:
            await call.edit(self.strings("no_users"))
            self._lock.pop(chat_id)
            return

        m = self.strings("processing_complete").format(
            sum([len(user_messages) for user_messages in data.values()]),
            len(data),
            len(restrict),
            self.strings(self.config["action"]),
        )

        for user in restrict:
            line = (
                "\n▫️ <a"
                f" href='tg://user?id={user}'>{utils.escape_html(names.get(user, user))}</a>"
                f" ({len(data[user])} {self.strings('messages')},"
                f" {round((time.time() - max(data[user])) / 3600, 1) if data[user] else 'n/a'} {self.strings('hrs')})"
            )
            if len(m + line) >= 4096:
                m += "\n..."
                break

            m += line

        await call.edit(
            m,
            reply_markup=[
                {
                    "text": self.strings("restrict"),
                    "callback": self._restrict,
                    "args": (chat_id, restrict, markup),
                },
                {
                    "text": self.strings("cancel"),
                    "callback": self._im_cancel,
                    "args": (chat_id,),
                },
            ],
        )

    async def _im_cancel(self, call: InlineCall, chat_id: int):
        self._lock.pop(chat_id)
        await call.edit(self.strings("processing_cancelled"))

    async def _restrict(
        self,
        call: InlineCall,
        chat_id: int,
        restrict: set,
        markup: dict,
    ):
        await call.edit(
            self.strings("applying_restrictions").format(
                len(restrict), self.strings(self.config["action"])
            ),
            reply_markup=markup,
        )
        for user_id in restrict:
            if self.config["action"] == "kick":
                await self._client.kick_participant(chat_id, user_id)
            else:
                await self._client.edit_permissions(
                    chat_id,
                    user_id,
                    until_date=0,
                    view_messages=False,
                    send_messages=False,
                    send_media=False,
                    send_stickers=False,
                    send_gifs=False,
                    send_games=False,
                    send_inline=False,
                    send_polls=False,
                    change_info=False,
                    invite_users=False,
                )

            await asyncio.sleep(3)

            if self._lock[chat_id].is_set():
                await call.edit(self.strings("processing_cancelled"))
                self._lock.pop(chat_id)
                return

        await call.edit(
            self.strings("restrictions_applied").format(
                self.strings(self.config["action"]),
                len(restrict),
            )
        )
        self._lock.pop(chat_id)

    @loader.command(ru_doc="Запустить чистку неактивных юзеров")
    async def inactive(self, message: Message):
        """Start inactive users cleaner"""
        if not self.config["inactive_time"] and not self.config["inactive_messages"]:
            await utils.answer(
                message,
                self.strings("config").format(
                    self.get_prefix(),
                    self.__class__.__name__,
                ),
            )
            return

        if utils.get_chat_id(message) in self._lock:
            await utils.answer(message, self.strings("processing_already"))
            return

        await self.inline.form(
            message=message,
            text=self.strings("confirm").format(
                (
                    f'{self.config["inactive_time"]} {self.strings("hrs")}'
                    if self.config["inactive_time"]
                    else "-"
                ),
                self.config["inactive_messages"] or "-",
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("start"),
                        "callback": self._start,
                        "args": (utils.get_chat_id(message),),
                    },
                    {"text": self.strings("cancel"), "action": "close"},
                ],
                [{"text": self.strings("configure"), "callback": self._configure}],
            ],
        )
