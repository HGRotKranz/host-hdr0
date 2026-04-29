#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/bulkcheck_icon.png
# meta banner: https://mods.hikariatama.ru/badges/bulkcheck.jpg
# meta developer: @rotkranz
# scope: hikka_only
# scope: hikka_min 1.2.10
# requires: requests

import requests
from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, utils


@loader.tds
class BulkCheckMod(loader.Module):
    """Check all members of chat for leaked numbers"""

    strings = {
        "name": "BulkCheck",
        "processing": (
            "<emoji document_id=5451732530048802485>⏳</emoji> <b>Processing...</b>"
        ),
        "no_pm": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>This command can be"
            " used only in chat</b>"
        ),
        "leaked": (
            "<emoji document_id=5465169893580086142>☎️</emoji> <b>Leaked numbers in"
            " current chat:</b>\n\n{}"
        ),
        "404": (
            "<emoji document_id=5465325710698617730>☹️</emoji> <b>No leaked numbers"
            " found here</b>"
        ),
    }

    strings_ru = {
        "processing": (
            "<emoji document_id=5451732530048802485>⏳</emoji> <b>Работаю...</b>"
        ),
        "no_pm": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Эту команду нужно"
            " выполнять в чате</b>"
        ),
        "leaked": (
            "<emoji document_id=5465169893580086142>☎️</emoji> <b>Слитые номера в этом"
            " чате:</b>\n\n{}"
        ),
        "404": (
            "<emoji document_id=5465325710698617730>☹️</emoji> <b>Тут нет слитых"
            " номеров</b>"
        ),
        "_cmd_doc_bulkcheck": "Проверить все участников чата на слитые номера",
        "_cls_doc": "Проверяет всех участников чата на слитые номера",
    }

    strings_de = {
        "processing": (
            "<emoji document_id=5451732530048802485>⏳</emoji> <b>Verarbeite...</b>"
        ),
        "no_pm": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Dieser Befehl"
            " kann nur"
            " in einem Chat verwendet werden</b>"
        ),
        "leaked": (
            "<emoji document_id=5465169893580086142>☎️</emoji> <b>Leaked Nummern in"
            " diesem Chat:</b>\n\n{}"
        ),
        "404": (
            "<emoji document_id=5465325710698617730>☹️</emoji> <b>Keine leaked Nummern"
            " in diesem Chat gefunden</b>"
        ),
        "_cmd_doc_bulkcheck": "Überprüfe alle Mitglieder des Chats auf leaked Nummern",
        "_cls_doc": "Überprüft alle Mitglieder des Chats auf leaked Nummern",
    }

    strings_hi = {
        "processing": (
            "<emoji document_id=5451732530048802485>⏳</emoji> <b>प्रोसेसिंग...</b>"
        ),
        "no_pm": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>यह कमांड केवल चैट में"
            " उपयोग किया जा सकता है</b>"
        ),
        "leaked": (
            "<emoji document_id=5465169893580086142>☎️</emoji> <b>वर्तमान चैट में लीक"
            " किए गए नंबर:</b>\n\n{}"
        ),
        "404": (
            "<emoji document_id=5465325710698617730>☹️</emoji> <b>यहां कोई लीक किए गए"
            " नंबर नहीं मिला</b>"
        ),
        "_cmd_doc_bulkcheck": "चैट के सभी सदस्यों को लीक किए गए नंबरों के लिए जांचें",
        "_cls_doc": "चैट के सभी सदस्यों को लीक किए गए नंबरों के लिए जांचता है",
    }

    strings_uz = {
        "processing": (
            "<emoji document_id=5451732530048802485>⏳</emoji> <b>Ishlamoqda...</b>"
        ),
        "no_pm": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Ushbu buyruq faqat"
            " guruhda ishlatilishi mumkin</b>"
        ),
        "leaked": (
            "<emoji document_id=5465169893580086142>☎️</emoji> <b>Joriy guruhda"
            " chiqarilgan raqamlar:</b>\n\n{}"
        ),
        "404": (
            "<emoji document_id=5465325710698617730>☹️</emoji> <b>Bu guruhda"
            " chiqarilgan raqamlar topilmadi</b>"
        ),
        "_cmd_doc_bulkcheck": (
            "Guruhning barcha a'zolarini chiqarilgan raqamlar uchun tekshirish"
        ),
        "_cls_doc": "Guruhning barcha a'zolarini chiqarilgan raqamlar uchun tekshiradi",
    }

    strings_tr = {
        "processing": (
            "<emoji document_id=5451732530048802485>⏳</emoji> <b>İşleniyor...</b>"
        ),
        "no_pm": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bu komut sadece"
            " sohbetlerde kullanılabilir</b>"
        ),
        "leaked": (
            "<emoji document_id=5465169893580086142>☎️</emoji> <b>Bu sohbetteki sızan"
            " numaralar:</b>\n\n{}"
        ),
        "404": (
            "<emoji document_id=5465325710698617730>☹️</emoji> <b>Bu sohbette sızan"
            " numara bulunamadı</b>"
        ),
        "_cmd_doc_bulkcheck": "Sohbetteki tüm üyeleri sızan numaralar için kontrol et",
        "_cls_doc": "Sohbetteki tüm üyeleri sızan numaralar için kontrol eder",
    }

    async def bcheckcmd(self, message: Message):
        """Bulk check using Murix database"""
        if message.is_private:
            await utils.answer(message, self.strings("no_pm"))
            return

        message = await utils.answer(message, self.strings("processing"))

        results = []
        async for member in self._client.iter_participants(message.peer_id):
            result = (
                await utils.run_sync(
                    requests.get,
                    f"http://api.murix.ru/eye?uid={member.id}&v=1.2",
                )
            ).json()
            if result["data"] != "NOT_FOUND":
                results += [
                    "<b>▫️ <a"
                    f' href="tg://user?id={member.id}">{utils.escape_html(get_display_name(member))}</a></b>:'
                    f" <code>+{result['data']}</code>"
                ]

        await utils.answer(
            message,
            (
                self.strings("leaked").format("\n".join(results))
                if results
                else self.strings("404")
            ),
        )
