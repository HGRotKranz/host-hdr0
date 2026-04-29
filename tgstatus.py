#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://img.icons8.com/cotton/344/like--v2.png
# meta developer: @rotkranz
# meta banner: https://mods.hikariatama.ru/badges/tgstatus.jpg
# scope: hikka_only
# scope: hikka_min 1.4.2

import logging
import time

from telethon.tl.functions.messages import (
    GetCustomEmojiDocumentsRequest,
    GetStickerSetRequest,
)
from telethon.tl.types import Message, MessageEntityCustomEmoji

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class TgStatus(loader.Module):
    """Rotates Telegram status for Telegram Premium users only"""

    strings = {
        "name": "TgStatus",
        "noargs": (
            "<emoji document_id=6053166094816905153>💀</emoji> <b>You must specify"
            " interval of status rotation and at least one custom emoji!</b>"
        ),
        "status_started": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Status rotation"
            " started!</b>\n\n<emoji document_id=5451732530048802485>⏳</emoji>"
            " <b>Interval: every {} minute(-s)</b>\n<b>Emojis: </b>{}"
        ),
        "status_stopped": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Status rotation"
            " stopped!</b>"
        ),
        "no_status": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Status rotation"
            " is not"
            " running!</b>"
        ),
    }

    strings_ru = {
        "noargs": (
            "<emoji document_id=6053166094816905153>💀</emoji> <b>Вы должны"
            " указать интервал смены статуса и хотя бы один кастомный эмодзи!</b>"
        ),
        "status_started": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Смена статуса"
            " запущена!</b>\n\n<emoji document_id=5451732530048802485>⏳</emoji>"
            " <b>Интервал: каждые {} минут(-ы)</b>\n<b>Эмодзи: </b>{}"
        ),
        "status_stopped": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Смена статуса"
            " остановлена!</b>"
        ),
        "no_status": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Смена статуса не"
            " запущена!</b>"
        ),
    }

    strings_de = {
        "noargs": (
            "<emoji document_id=6053166094816905153>💀</emoji> <b>Du musst"
            " einen Intervall für den Statuswechsel angeben und mindestens einen"
            " benutzerdefinierten Emoji!</b>"
        ),
        "status_started": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Statuswechsel"
            " gestartet!</b>\n\n<emoji document_id=5451732530048802485>⏳</emoji>"
            " <b>Intervall: alle {} Minute(n)</b>\n<b>Emojis: </b>{}"
        ),
        "status_stopped": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Statuswechsel"
            " gestoppt!</b>"
        ),
        "no_status": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Es läuft"
            " kein Statuswechsel!</b>"
        ),
    }

    strings_hi = {
        "noargs": (
            "<emoji document_id=6053166094816905153>💀</emoji> <b>आपको स्थिति रोटेशन के"
            " लिए इंटरवल और कम से कम एक कस्टम इमोजी निर्दिष्ट करना होगा!</b>"
        ),
        "status_started": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>स्थिति रोटेशन शुरू हो"
            " गया!</b>\n\n<emoji document_id=5451732530048802485>⏳</emoji> <b>अंतराल:"
            " प्रत्येक {} मिनट(-s)</b>\n<b>इमोजी: </b>{}"
        ),
        "status_stopped": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>स्थिति रोटेशन बंद हो"
            " गया!</b>"
        ),
        "no_status": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>स्थिति रोटेशन शुरू"
            " नहीं हुआ है!</b>"
        ),
    }

    strings_tr = {
        "noargs": (
            "<emoji document_id=6053166094816905153>💀</emoji> <b>Durum döngüsü için"
            " bir döngü süresi ve en az bir özel emoji belirtmelisin!</b>"
        ),
        "status_started": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Durum döngüsü"
            " başladı!</b>\n\n<emoji document_id=5451732530048802485>⏳</emoji>"
            " <b>Döngü"
            " süresi: her {} dakika</b>\n<b>Emojiler: </b>{}"
        ),
        "status_stopped": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Durum döngüsü"
            " durduruldu!</b>"
        ),
        "no_status": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Durum döngüsü"
            " çalışmıyor!</b>"
        ),
    }

    strings_uz = {
        "noargs": (
            "<emoji document_id=6053166094816905153>💀</emoji> <b>Savol javobi"
            " uchun vaqt oraligini va kamida bitta maxsus emoji belgilang!</b>"
        ),
        "status_started": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Savol javobi"
            " boshlandi!</b>\n\n<emoji document_id=5451732530048802485>⏳</emoji>"
            " <b>Oraliq: har {} minut(-lar)</b>\n<b>Emojilar: </b>{}"
        ),
        "status_stopped": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Savol javobi"
            " to'xtatildi!</b>"
        ),
        "no_status": (
            "<emoji document_id=5789838291234720526>💸</emoji> <b>Savol javobi"
            " boshlanmagan!</b>"
        ),
    }

    async def client_ready(self):
        if not self._client.hikka_me.premium:
            raise loader.LoadError("⭐️ This module is for Telegram Premium only!")

        self.status = self.pointer("status", [])
        self.status_loop.start()

    @loader.loop(interval=1)
    async def status_loop(self):
        if (
            not self.status
            or not self.get("interval")
            or self.get("last_change", 0) + self.get("interval") > time.time()
        ):
            return

        await self._client.set_status(self.status[self.get("current_status", 0)])
        logger.debug(f"Status changed to {self.status[self.get('current_status', 0)]}")
        self.set("current_status", self.get("current_status", 0) + 1)

        if self.get("current_status") >= len(self.status):
            self.set("current_status", 0)

        self.set("last_change", int(time.time()))

    @loader.command(
        ru_doc=(
            "<кастомные эмодзи для статуса> <интервал в минутах> - Запустить ротацию"
            " статуса с интервалом в минутах"
        ),
        de_doc=(
            "<benutzerdefinierte Emojis für den Status> <Intervall in Minuten> - Starte"
            " den Status-Rotationszyklus mit einem Intervall in Minuten"
        ),
        tr_doc=(
            "<özel emoji durumu için> <dakika aralığı> - Dakika aralığı ile"
            " durum döngüsünü başlat"
        ),
        uz_doc=(
            "<status uchun maxsus emojilar> <daqiqa oraligi> - Daqiqa oraligi bilan"
            " savol javobini ishga tushirish"
        ),
        hi_doc=(
            "<स्थिति के लिए कस्टम इमोजी> <मिनट अंतराल> - मिनट अंतराल के साथ"
            " स्थिति रोटेशन चक्र शुरू करें"
        ),
    )
    async def tgstatus(self, message: Message):
        """<custom emojis for statuses> <time to rotate in minutes> - Start status rotation with interval in minutes"""
        args = utils.get_args_raw(message)
        args = "".join(s for s in args if s.isdigit())
        if not args or not any(
            isinstance(entity, MessageEntityCustomEmoji) for entity in message.entities
        ):
            await utils.answer(message, self.strings("noargs"))
            return

        self.status.clear()
        self.status.extend(
            [
                entity.document_id
                for entity in message.entities
                if isinstance(entity, MessageEntityCustomEmoji)
            ]
        )
        self.set("interval", int(args) * 60)
        self.set("last_change", 0)
        self.set("current_status", 0)
        await utils.answer(
            message,
            self.strings("status_started").format(
                args,
                "".join(
                    f"<emoji document_id={emoji.document_id}>▫️</emoji>"
                    for emoji in message.entities
                    if isinstance(emoji, MessageEntityCustomEmoji)
                ),
            ),
        )

    @loader.command(
        ru_doc=(
            "<кастомные эмодзи для получения паков> <интервал в минутах> - Запустить"
            " ротацию статуса с интервалом в минутах, используя полный пак указанных"
            " эмодзи"
        ),
        de_doc=(
            "<benutzerdefinierte Emojis für das Erhalten von Paketen> <Intervall in"
            " Minuten> - Starte den Status-Rotationszyklus mit einem Intervall in"
            " Minuten, indem du das volle Paket der angegebenen Emojis verwendest"
        ),
        tr_doc=(
            "<emoji paketleri almak için özel emoji> <dakika aralığı> - Dakika aralığı"
            " ile belirtilen emoji paketini kullanarak durum döngüsünü başlat"
        ),
        uz_doc=(
            "<emoji paketlarini olish uchun maxsus emojilar> <daqiqa oraligi> - Daqiqa"
            " oraligi bilan belgilangan emoji paketini ishlatib savol javobini ishga"
            " tushirish"
        ),
        hi_doc=(
            "<पैकेट प्राप्त करने के लिए कस्टम इमोजी> <मिनट अंतराल> - मिनट अंतराल"
            " के साथ निर्दिष्ट इमोजी का पूरा पैकेट उपयोग करके स्थिति रोटेशन चक्र"
            " शुरू करें"
        ),
    )
    async def tgstatuspack(self, message: Message):
        """<custom emojis for pack search> <time to rotate in minutes> - Start status rotation with interval in minutes using full pack of specified emojis"""
        args = utils.get_args_raw(message)
        args = "".join(s for s in args if s.isdigit())
        if not args or not any(
            isinstance(entity, MessageEntityCustomEmoji) for entity in message.entities
        ):
            await utils.answer(message, self.strings("noargs"))
            return

        self.status.clear()
        self.status.extend(
            utils.array_sum(
                [
                    [
                        emoji.id
                        for emoji in (
                            await self._client(GetStickerSetRequest(stickerset, hash=0))
                        ).documents
                    ]
                    for stickerset in filter(
                        lambda x: x,
                        [
                            next(
                                (
                                    attr.stickerset
                                    for attr in emoji.attributes
                                    if hasattr(attr, "stickerset")
                                ),
                                None,
                            )
                            for emoji in await self._client(
                                GetCustomEmojiDocumentsRequest(
                                    [
                                        entity.document_id
                                        for entity in message.entities
                                        if isinstance(entity, MessageEntityCustomEmoji)
                                    ]
                                )
                            )
                        ],
                    )
                ]
            )
        )
        self.set("interval", int(args) * 60)
        self.set("last_change", 0)
        self.set("current_status", 0)
        await utils.answer(
            message,
            self.strings("status_started").format(
                args,
                "".join(
                    f"<emoji document_id={emoji}>▫️</emoji>" for emoji in self.status
                ),
            ),
        )

    @loader.command(
        ru_doc="Остановить статус",
        de_doc="Stoppe den Status",
        tr_doc="Durum durdur",
        uz_doc="Savol javobini to'xtatish",
        hi_doc="स्थिति रोकें",
    )
    async def untgstatus(self, message: Message):
        """Stop status rotation"""
        if not self.status:
            await utils.answer(message, self.strings("no_status"))
            return

        self.status.clear()
        self.set("interval", 0)
        self.set("last_change", 0)
        self.set("current_status", 0)

        await utils.answer(message, self.strings("status_stopped"))
