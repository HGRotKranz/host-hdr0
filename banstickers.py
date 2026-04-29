__version__ = (2, 0, 0)

#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒 Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://img.icons8.com/fluency/344/cancel-2.png
# meta developer: @rotkranz
# meta banner: https://mods.hikariatama.ru/badges/banstickers.jpg
# scope: hikka_only
# scope: hikka_min 1.3.3
# requires: aiofile Pillow

import asyncio
import io
import logging
import math
import operator
import os
import time
from functools import reduce

from aiofile import async_open
from PIL import Image, ImageChops
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import Message

from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class BanStickers(loader.Module):
    """Bans stickerpacks, stickers and gifs in chat"""

    strings = {
        "name": "BanStickers",
        "args": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Reply to sticker is"
            " required</b>"
        ),
        "sticker_banned": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>This sticker is now"
            " banned in current chat</b>"
        ),
        "pack_banned": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>{} sticker(-s) from"
            " pack {} are now banned in current chat</b>"
        ),
        "wait": (
            "<emoji document_id='5451732530048802485'>⏳</emoji> <b>Banning stickers"
            " from this pack in current chat...</b>"
        ),
        "sticker_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>This sticker is not"
            " banned in current chat</b>"
        ),
        "sticker_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>This sticker is no"
            " longer banned in current chat</b>"
        ),
        "pack_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>{} / {} sticker(-s)"
            " from pack {} are no longer banned in current chat</b>"
        ),
        "pack_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>This pack is not"
            " banned in current chat</b>"
        ),
        "no_restrictions": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>This chat has"
            " no restrictions</b>"
        ),
        "all_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>All stickers are"
            " unbanned in current chat</b>"
        ),
        "already_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Animated and video"
            " stickers are already restricted</b>"
        ),
        "not_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Animated stickers"
            " are not restricted</b>"
        ),
        "animations_restricted": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Animated and video"
            " stickers are now restricted in current chat</b>"
        ),
        "animations_unrestricted": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Animated stickers"
            " are no longer restricted</b>"
        ),
    }

    strings_ru = {
        "args": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Нужен ответ на"
            " стикер</b>"
        ),
        "sticker_banned": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>Этот стикер теперь"
            " запрещен в текущем чате</b>"
        ),
        "pack_banned": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>{} стикер(-ов) из"
            " пака {} теперь запрещены в текущем чате</b>"
        ),
        "wait": (
            "<emoji document_id='5451732530048802485'>⏳</emoji> <b>Запрещаю"
            " стикеры из этого пака в текущем чате...</b>"
        ),
        "sticker_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Этот стикер не"
            " запрещен в текущем чате</b>"
        ),
        "sticker_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Этот стикер больше"
            " не запрещен в текущем чате</b>"
        ),
        "pack_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>{} / {} стикер(-ов)"
            " из пака {} больше не запрещены в текущем чате</b>"
        ),
        "pack_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Этот пак не запре"
            "щен в текущем чате</b>"
        ),
        "no_restrictions": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>В текущем чате нет"
            " ограничений</b>"
        ),
        "all_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Все стикеры"
            " разблокированы в текущем чате</b>"
        ),
        "already_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Анимированные и"
            " видео стикеры уже запрещены</b>"
        ),
        "not_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Анимированные"
            " стикеры не запрещены</b>"
        ),
        "animations_restricted": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Анимированные и"
            " видео стикеры запрещены в текущем чате</b>"
        ),
        "animations_unrestricted": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Анимированные"
            " стикеры больше не запрещены</b>"
        ),
    }

    strings_de = {
        "args": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Antwort auf einen"
            " Sticker erforderlich</b>"
        ),
        "sticker_banned": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>Dieser Sticker ist"
            " nun im aktuellen Chat gesperrt</b>"
        ),
        "pack_banned": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>{} Sticker aus dem"
            " Pack {} sind nun im aktuellen Chat gesperrt</b>"
        ),
        "wait": (
            "<emoji document_id='5451732530048802485'>⏳</emoji> <b>Sticker aus diesem"
            " Pack werden im aktuellen Chat gesperrt...</b>"
        ),
        "sticker_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Dieser Sticker ist"
            " nicht im aktuellen Chat gesperrt</b>"
        ),
        "sticker_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Dieser Sticker ist"
            " nun wieder im aktuellen Chat erlaubt</b>"
        ),
        "pack_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>{} / {} Sticker aus"
            " dem Pack {} sind nun wieder im aktuellen Chat erlaubt</b>"
        ),
        "pack_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Dieses Pack ist im"
            " aktuellen Chat nicht gesperrt</b>"
        ),
        "no_restrictions": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Im aktuellen Chat"
            " gibt es keine Einschränkungen</b>"
        ),
        "all_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Alle Sticker"
            " sind im"
            " aktuellen Chat wieder erlaubt</b>"
        ),
        "already_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Animierte Sticker"
            " sind bereits gesperrt</b>"
        ),
        "not_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Animierte Sticker"
            " sind nicht gesperrt</b>"
        ),
        "animations_restricted": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Animierte Sticker"
            " sind nun im aktuellen Chat gesperrt</b>"
        ),
        "animations_unrestricted": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Animierte Sticker"
            " sind nun wieder im aktuellen Chat erlaubt</b>"
        ),
    }

    strings_hi = {
        "args": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>एक स्टिकर पर उत्तर"
            " आवश्यक है</b>"
        ),
        "sticker_banned": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>इस स्टिकर को वर्तमान"
            " चैट में प्रतिबंधित किया गया है</b>"
        ),
        "pack_banned": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>{1} पैक से {0}"
            " स्टिकर वर्तमान चैट में प्रतिबंधित किए गए हैं</b>"
        ),
        "wait": (
            "<emoji document_id='5451732530048802485'>⏳</emoji> <b>वर्तमान चैट में {1}"
            " पैक से स्टिकर प्रतिबंधित किए जा रहे हैं...</b>"
        ),
        "sticker_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>वर्तमान चैट में इस"
            " स्टिकर को प्रतिबंधित नहीं किया गया है</b>"
        ),
        "sticker_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>इस स्टिकर को वर्तमान"
            " चैट में प्रतिबंधित नहीं किया गया है</b>"
        ),
        "pack_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>{1} पैक से {0}"
            " स्टिकर वर्तमान चैट में प्रतिबंधित नहीं किए गए हैं</b>"
        ),
        "pack_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>वर्तमान चैट में यह"
            " पैक प्रतिबंधित नहीं किया गया है</b>"
        ),
        "no_restrictions": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>वर्तमान चैट में कोई"
            " प्रतिबंध नहीं है</b>"
        ),
        "all_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>वर्तमान चैट में सभी"
            " स्टिकर प्रतिबंधित नहीं किए गए हैं</b>"
        ),
        "already_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>आगे बढ़ने के लिए"
            " पहले से ही प्रतिबंधित किए गए हैं</b>"
        ),
        "not_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>इस स्टिकर को पहले"
            " से ही प्रतिबंधित नहीं किया गया है</b>"
        ),
        "already_unrestricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>इस स्टिकर को पहले"
            " से ही प्रतिबंधित नहीं किया गया है</b>"
        ),
        "animations_restricted": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>वर्तमान चैट में"
            " एनीमेटेड स्टिकर अब प्रतिबंधित हैं</b>"
        ),
        "animations_unrestricted": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>वर्तमान चैट में"
            " एनीमेटेड स्टिकर अब प्रतिबंधित नहीं हैं</b>"
        ),
    }

    strings_uz = {
        "pack_banned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>{1} pakidan {0}"
            " stikerlar cheklangan</b>"
        ),
        "sticker_banned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Stiker"
            " cheklangan</b>"
        ),
        "not_a_pack": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Bu paket emas</b>"
        ),
        "pack_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Ushbu paket"
            " cheklangan emas</b>"
        ),
        "sticker_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Ushbu stiker"
            " cheklangan emas</b>"
        ),
        "sticker_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Stiker cheklangan"
            " emas</b>"
        ),
        "pack_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>{1} pakidan {0}"
            " stikerlar cheklangan emas</b>"
        ),
        "no_restrictions": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Ushbu chatda"
            " cheklangan stikerlar yo'q</b>"
        ),
        "all_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Ushbu chatda barcha"
            " stikerlar cheklangan emas</b>"
        ),
        "already_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Ushbu stiker oldin"
            " cheklangan</b>"
        ),
        "not_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Ushbu stiker"
            " cheklangan emas</b>"
        ),
        "already_unrestricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Ushbu stiker oldin"
            " cheklangan emas</b>"
        ),
        "animations_restricted": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>Ushbu chatda"
            " animatsiya stikerlari cheklangan</b>"
        ),
        "animations_unrestricted": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Ushbu chatda"
            " animatsiya stikerlari cheklangan emas</b>"
        ),
    }

    strings_tr = {
        "pack_banned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>{1} paketinden {0}"
            " çıkartma yasaklandı</b>"
        ),
        "sticker_banned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Çıkartma"
            " yasaklandı</b>"
        ),
        "not_a_pack": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Bu bir paket"
            " değil</b>"
        ),
        "pack_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Bu paket"
            " yasaklanmamış</b>"
        ),
        "sticker_not_banned": (
            "<emoji document_id='5436162517686557387'>😵</emoji> <b>Bu çıkartma"
            " yasaklanmamış</b>"
        ),
        "sticker_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Çıkartma"
            " yasaklanmamış</b>"
        ),
        "pack_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>{1} paketinden {0}"
            " çıkartma yasaklanmamış</b>"
        ),
        "no_restrictions": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Bu sohbette"
            " yasaklanmış çıkartma yok</b>"
        ),
        "all_unbanned": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Bu sohbette tüm"
            " çıkartmalar yasaklanmamış</b>"
        ),
        "already_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Bu çıkartma zaten"
            " yasaklanmış</b>"
        ),
        "not_restricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Bu çıkartma"
            " yasaklanmamış</b>"
        ),
        "already_unrestricted": (
            "<emoji document_id='5436040291507247633'>🎉</emoji> <b>Bu çıkartma zaten"
            " yasaklanmamış</b>"
        ),
        "animations_restricted": (
            "<emoji document_id='6037557968914877661'>🛡</emoji> <b>Bu sohbette"
            " animasyonlu çıkartmalar yasaklanmış</b>"
        ),
        "animations_unrestricted": (
            "<emoji document_id='5472308992514464048'>🔐</emoji> <b>Bu sohbette"
            " animasyonlu çıkartmalar yasaklanmamış</b>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "rms_threshold",
                4.0,
                (
                    "The lower this value is - the more light the detection will be."
                    " 0.0 - Full match, 4.0 - approximate match"
                ),
                validator=loader.validators.Float(maximum=10.0),
            ),
            loader.ConfigValue(
                "bantime",
                180,
                (
                    "Once the user sent forbidden sticker, he will be restricted from"
                    " sending more for this amount of seconds"
                ),
                validator=loader.validators.Integer(minimum=60),
            ),
        )

    async def client_ready(self):
        self._banlist = self.pointer("banlist", {})
        self._bananim = self.pointer("bananim", [])
        dir_path = os.path.abspath(
            os.path.join(utils.get_base_dir(), "..", "loaded_modules")
        )
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)

        dir_path = os.path.join(dir_path, "banmedia")
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)

        self._db_path = dir_path
        self._cache = {}
        self._filecache = {}
        for file in os.listdir(self._db_path):
            async with async_open(os.path.join(self._db_path, file), "rb") as f:
                self._cache[file] = await f.read()

    @staticmethod
    def rmsdiff(image_1: Image, image_2: Image) -> float:
        "Calculate the root-mean-square difference between two images"
        # https://stackoverflow.com/a/11818358/19170642

        try:
            h = ImageChops.difference(image_1, image_2).histogram()
        except ValueError:
            return 100.0

        return math.sqrt(
            reduce(operator.add, map(lambda h, i: h * (i**2), h, range(256)))
            / (float(image_1.size[0]) * image_1.size[1])
        )

    async def _add_cache(self, sticker_id: int, bytes_: bytes):
        if not os.path.isfile(os.path.join(self._db_path, str(sticker_id))):
            async with async_open(
                os.path.join(self._db_path, str(sticker_id)), "wb"
            ) as f:
                await f.write(bytes_)

        self._cache[str(sticker_id)] = bytes_

    async def _remove_cache(self, sticker_id: int):
        if os.path.isfile(os.path.join(self._db_path, str(sticker_id))):
            os.remove(os.path.join(self._db_path, str(sticker_id)))

        if str(sticker_id) in self._cache:
            self._cache.pop(str(sticker_id))

    @loader.command(
        ru_doc="<ответ на стикер> - Запретить стикер в текущем чате",
        de_doc="<auf Antwort auf Sticker> - Verbotene Sticker in diesem Chat",
        hi_doc="<उत्तर दिए गए स्टिकर पर> - इस चैट में अनुमति नहीं देने वाले स्टिकर",
        uz_doc="<stickerga javob> - Joriy suhbatda stikerni taqiqlash",
        tr_doc="<sticker'a yanıt> - Bu sohbette yasaklanmış çıkartma",
    )
    async def banstick(self, message: Message):
        """<reply to sticker> - Ban sticker in current chat"""
        reply = await message.get_reply_message()
        if not reply or not reply.sticker:
            await utils.answer(message, self.strings("args"))
            return

        chat_id = str(utils.get_chat_id(message))
        self._banlist.setdefault(chat_id, []).append(reply.sticker.id)
        self._banlist[chat_id] = list(set(self._banlist[chat_id]))

        if reply.sticker.mime_type.startswith("image"):
            await self._add_cache(reply.sticker.id, await reply.download_media(bytes))

        await utils.answer(message, self.strings("sticker_banned"))

    @loader.command(
        ru_doc="<ответ на стикер> - Запретить весь стикерпак в текущем чате",
        de_doc="<auf Antwort auf Sticker> - Verbotene Stickerpack in diesem Chat",
        hi_doc="<उत्तर दिए गए स्टिकर पर> - इस चैट में अनुमति नहीं देने वाले स्टिकर पैक",
        uz_doc="<stickerga javob> - Joriy suhbatda stikerni taqiqlash",
        tr_doc="<sticker'a yanıt> - Bu sohbette yasaklanmış çıkartma paketi",
    )
    async def banpack(self, message: Message):
        """<reply to sticker> - Ban the whole stickerpack in current chat"""
        reply = await message.get_reply_message()
        if not reply or not reply.sticker:
            await utils.answer(message, self.strings("args"))
            return

        message = await utils.answer(message, self.strings("wait"))
        stickerset = await self._client(
            GetStickerSetRequest(
                next(
                    attr.stickerset
                    for attr in reply.sticker.attributes
                    if hasattr(attr, "stickerset")
                ),
                hash=0,
            )
        )

        stickers = stickerset.documents
        chat_id = str(utils.get_chat_id(message))

        for sticker in stickers:
            self._banlist.setdefault(chat_id, []).append(sticker.id)
            if sticker.mime_type.startswith("image"):
                await self._add_cache(
                    sticker.id,
                    await self._client.download_file(sticker, bytes),
                )
                await asyncio.sleep(1)  # Light FW protection

        self._banlist[chat_id] = list(set(self._banlist[chat_id]))

        await utils.answer(
            message,
            self.strings("pack_banned").format(
                len(stickers),
                utils.escape_html(stickerset.set.title),
            ),
        )

    @loader.command(
        ru_doc="<ответ на стикер> - Разбанить стикер в текущем чате",
        de_doc="<auf Antwort auf Sticker> - Entbanne Sticker in diesem Chat",
        hi_doc="<उत्तर दिए गए स्टिकर पर> - इस चैट में अनुमति देने वाले स्टिकर",
        uz_doc="<stickerga javob> - Joriy suhbatda stikerni taqiqlash",
        tr_doc="<sticker'a yanıt> - Bu sohbette yasaklanmış çıkartma",
    )
    async def unbanstick(self, message: Message):
        """<reply to sticker> - Unban sticker in current chat"""
        reply = await message.get_reply_message()
        if not reply or not reply.sticker:
            await utils.answer(message, self.strings("args"))
            return

        chat_id = str(utils.get_chat_id(message))
        if reply.sticker.id not in self._banlist.get(chat_id, []):
            await utils.answer(message, self.strings("sticker_not_banned"))
            return

        self._banlist[chat_id].remove(reply.sticker.id)
        if reply.sticker.mime_type.startswith("image"):
            await self._remove_cache(reply.sticker.id)

        await utils.answer(message, self.strings("sticker_unbanned"))

    @loader.command(
        ru_doc="<ответ на стикер> - Разбанить весь стикерпак в текущем чате"
    )
    async def unbanpack(self, message: Message):
        """<reply to sticker> - Unban the whole stickerpack in current chat"""
        reply = await message.get_reply_message()
        if not reply or not reply.sticker:
            await utils.answer(message, self.strings("args"))
            return

        message = await utils.answer(message, self.strings("wait"))
        stickerset = await self._client(
            GetStickerSetRequest(
                next(
                    attr.stickerset
                    for attr in reply.sticker.attributes
                    if hasattr(attr, "stickerset")
                ),
                hash=0,
            )
        )

        stickers = stickerset.documents
        chat_id = str(utils.get_chat_id(message))

        unbanned = 0

        for sticker in stickers:
            if sticker.id in self._banlist.get(chat_id, []):
                self._banlist[chat_id].remove(sticker.id)
                if sticker.mime_type.startswith("image"):
                    await self._remove_cache(sticker.id)
                unbanned += 1

        if not unbanned:
            await utils.answer(message, self.strings("pack_not_banned"))
            return

        await utils.answer(
            message,
            self.strings("pack_unbanned").format(
                unbanned,
                len(stickers),
                utils.escape_html(stickerset.set.title),
            ),
        )

    @loader.command(
        ru_doc="Убрать все ограничения в текущем чате",
        de_doc="Entferne alle Einschränkungen in diesem Chat",
        hi_doc="इस चैट में सभी सीमाएं निकालें",
        uz_doc="Joriy suhbatda barcha cheklarni olib tashlang",
        tr_doc="Bu sohbetteki tüm yasaklamaları kaldırın",
    )
    async def unbanall(self, message: Message):
        """Remove all restrictions in current chat"""
        chat_id = str(utils.get_chat_id(message))
        if not self._banlist.get(chat_id, []):
            await utils.answer(message, self.strings("no_restrictions"))
            return

        for sticker in self._banlist.pop(chat_id):
            await self._remove_cache(sticker)

        await utils.answer(message, self.strings("all_unbanned"))

    @loader.command(
        ru_doc="Запретить анимированные и видео стикеры в этом чате",
        de_doc="Verbiete animierte und Video-Sticker in diesem Chat",
        hi_doc="इस चैट में एनीमेटेड और वीडियो स्टिकर्स को अस्वीकार करें",
        uz_doc="Bu suhbatda animatsiya va video stikerni taqiqlang",
        tr_doc="Bu sohbette animasyonlu ve video çıkartmaları yasaklayın",
    )
    async def bananim(self, message: Message):
        """Restrict animated stickers in current chat"""
        chat_id = str(utils.get_chat_id(message))
        if chat_id in self._bananim:
            await utils.answer(message, self.strings("already_restricted"))
            return

        self._bananim.append(chat_id)
        await utils.answer(message, self.strings("animations_restricted"))

    @loader.command(
        ru_doc="Разблокировать анимированные и видео стикеры в этом чате",
        de_doc=(
            "Entferne die Einschränkung für animierte und Video-Sticker in diesem Chat"
        ),
        hi_doc="इस चैट में एनीमेटेड और वीडियो स्टिकर्स की प्रतिबंध निकालें",
        uz_doc="Bu suhbatda animatsiya va video stikerni taqiqlashni olib tashlang",
        tr_doc="Bu sohbette animasyonlu ve video çıkartmaları yasaklamasını kaldırın",
    )
    async def unbananim(self, message: Message):
        """Unrestrict animated stickers in current chat"""
        chat_id = str(utils.get_chat_id(message))
        if chat_id not in self._bananim:
            await utils.answer(message, self.strings("not_restricted"))
            return

        self._bananim.remove(chat_id)
        await utils.answer(message, self.strings("animations_unrestricted"))

    @loader.watcher("in", only_stickers=True, only_groups=True)
    async def watcher(self, message: Message):
        chat_id = str(utils.get_chat_id(message))
        if not self._banlist.get(chat_id):
            return

        async def _restrict():
            nonlocal message
            await message.delete()
            await self._client.edit_permissions(
                message.peer_id,
                message.sender_id,
                until_date=time.time() + self.config["bantime"],
                send_stickers=False,
            )

        if not message.sticker.mime_type.startswith("image"):
            if chat_id in self._bananim or message.sticker.id in self._banlist[chat_id]:
                await _restrict()

            return

        if message.sticker.id in self._filecache:
            file = self._filecache[message.sticker.id]
        else:
            file = await message.download_media(bytes)
            self._filecache[message.sticker.id] = file

        image = Image.open(io.BytesIO(file))
        for sticker_id, bytes_ in self._cache.items():
            res = await utils.run_sync(
                self.rmsdiff,
                image,
                Image.open(io.BytesIO(bytes_)),
            )
            if res < self.config["rms_threshold"]:
                await self._add_cache(sticker_id, file)
                return await _restrict()
