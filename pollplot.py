#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://static.dan.tatar/pollplot_icon.png
# meta banner: https://mods.hikariatama.ru/badges/pollplot.jpg
# requires: matplotlib
# meta developer: @rotkranz
# scope: hikka_only
# scope: hikka_min 1.2.10

import io

import matplotlib.pyplot as plt
from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class PollPlotMod(loader.Module):
    """Visualises polls as plots"""

    strings = {
        "name": "PollPlot",
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Reply to a poll is"
            " required!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>This poll has not"
            " answers yet.</b>"
        ),
    }

    strings_ru = {
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Нужен ответ на"
            " опрос!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>В этом опросе"
            " пока что"
            " нет участников.</b>"
        ),
        "_cmd_doc_plot": "<reply> - Создать визуализацию опроса",
        "_cls_doc": "Визуализирует опросы в виде графиков",
    }

    strings_de = {
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Antwort auf eine"
            " Umfrage erforderlich!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>Diese Umfrage hat"
            " noch"
            " keine Antworten.</b>"
        ),
        "_cmd_doc_plot": "<reply> - Erstelle eine Visualisierung von Umfragen",
        "_cls_doc": "Visualisiert Umfragen als Diagramme",
    }

    strings_hi = {
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>एक पोल पर जवाब आवश्यक"
            " है!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>इस पोल में अभी तक कोई"
            " उत्तर नहीं है।</b>"
        ),
        "_cmd_doc_plot": "<reply> - पोल को बनाने के लिए प्लॉट करें",
        "_cls_doc": "पोल को प्लॉट के रूप में दर्शाता है",
    }

    strings_uz = {
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Javob berilgan savol"
            " kerak!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>Ushbu savolda hali"
            " hech qanday javob yo'q.</b>"
        ),
        "_cmd_doc_plot": "<reply> - Savolni chizishga o'tkazish",
        "_cls_doc": "Savollarni chizishlar shaklida ko'rsatadi",
    }

    strings_tr = {
        "no_reply": (
            "<emoji document_id=5312526098750252863>🚫</emoji> <b>Bir anket yanıtı"
            " gerekli!</b>"
        ),
        "no_answers": (
            "<emoji document_id=5197183257367552085>😢</emoji> <b>Bu anket henüz cevap"
            " yok.</b>"
        ),
        "_cmd_doc_plot": "<yanıt> - Bir anketi çizimden oluşturun",
        "_cls_doc": "Anketleri çizimler şeklinde gösterir",
    }

    async def plotcmd(self, message: Message):
        """<reply> - Create plot from poll"""
        reply = await message.get_reply_message()
        if not reply or not getattr(reply, "poll", False):
            await utils.answer(message, self.strings("no_reply"))
            return

        sizes = [i.voters for i in reply.poll.results.results]

        if not sum(sizes):
            await utils.answer(message, self.strings("no_answers"))
            return

        labels = [
            f"{a.text} [{sizes[i]}] ({round(sizes[i] / sum(sizes) * 100, 1)}%)"
            for i, a in enumerate(reply.poll.poll.answers)
        ]

        explode = [0.05] * len(sizes)
        fig1, ax1 = plt.subplots()
        ax1.pie(
            sizes,
            explode=explode,
            labels=labels,
            textprops={"color": "white", "size": "large"},
        )
        buf = io.BytesIO()
        fig1.patch.set_facecolor("#303841")
        fig1.savefig(buf)
        buf.seek(0)

        await self._client.send_file(message.peer_id, buf.getvalue(), reply_to=reply)

        if message.out:
            await message.delete()
