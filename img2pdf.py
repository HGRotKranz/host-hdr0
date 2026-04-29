#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# scope: hikka_min 1.2.10

# meta pic: https://img.icons8.com/stickers/500/000000/pdf.png
# meta banner: https://mods.hikariatama.ru/badges/img2pdf.jpg
# meta developer: @rotkranz
# requires: Pillow

import io

from PIL import Image, UnidentifiedImageError
from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class Img2PdfMod(loader.Module):
    """Packs images to pdf"""

    strings = {
        "name": "Img2Pdf",
        "processing": (
            "<emoji document_id=5307865634032329170>🫥</emoji> <b>Processing"
            " files...</b>"
        ),
    }
    strings_ru = {
        "processing": (
            "<emoji document_id=5307865634032329170>🫥</emoji> <b>Обрабатываю"
            " файлы...</b>"
        )
    }
    strings_es = {
        "processing": (
            "<emoji document_id=5307865634032329170>🫥</emoji> <b>Procesando"
            " archivos...</b>"
        )
    }
    strings_de = {
        "processing": (
            "<emoji document_id=5307865634032329170>🫥</emoji> <b>Dateien werden"
            " verarbeitet...</b>"
        )
    }
    strings_tr = {
        "processing": (
            "<emoji document_id=5307865634032329170>🫥</emoji> <b>Dosyalar"
            " işleniyor...</b>"
        )
    }

    @loader.unrestricted
    async def img2pdfcmd(self, message: Message):
        """<filename | optional> - Pack images into pdf"""
        try:
            start_offset = (
                message.id if message.media else (await message.get_reply_message()).id
            )
        except Exception:
            return await utils.answer(message, self.strings("no_file"))

        message = await utils.answer(message, self.strings("processing"))

        images = []

        async for ms in self._client.iter_messages(
            message.peer_id, offset_id=start_offset - 1, reverse=True
        ):
            if not ms.media:
                break
            im = await self._client.download_file(ms.media, bytes)
            try:
                images.append(Image.open(io.BytesIO(im)))
            except UnidentifiedImageError:
                break

        first_image, images = images[0], images[1:]
        file = io.BytesIO()
        first_image.save(
            file,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=images,
        )
        f = io.BytesIO(file.getvalue())
        f.name = utils.get_args_raw(message) or "packed_images.pdf"
        await self._client.send_file(message.peer_id, f)
        await message.delete()
