#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# meta pic: https://img.icons8.com/color/480/000000/angry--v1.png
# meta banner: https://mods.hikariatama.ru/badges/insult.jpg
# meta developer: @rotkranz
# scope: hikka_min 1.2.10

import random

from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class PoliteInsultMod(loader.Module):
    """If you need to insult but to be intelligent"""

    strings = {
        "name": "PoliteInsult",
        "insult": (
            "<emoji document_id=5373123633415723713>🤬</emoji> {} you are {} {} {} {}"
        ),
        "adjectives_start": [
            "temperamental",
            "rude",
            "silly to me",
            "arrogant",
            "non-individualistic",
            "undisciplined",
            "unprofessional",
            "irresponsible",
            "reckless",
            "indifferent to meser",
        ],
        "nouns": ["participant of this group chat", "this world citizen"],
        "starts": [
            (
                "I don't want to jump to conclusions and I certainly can't claim, and"
                " this is my subjective opinion, but"
            ),
            (
                "Having analyzed the situation, I can express my subjective opinion. It"
                " lies in the fact that"
            ),
            (
                "Not trying to make anyone feel bad, but just expressing my humble"
                " point of view, which does not affect other people's points of view, I"
                " can say that"
            ),
            (
                "Without intending to affect any social minorities, I would like to say"
                " that"
            ),
        ],
    }

    strings_ru = {
        "insult": (
            "<emoji document_id=5373123633415723713>🤬</emoji> {} ты - {} {} {} {}"
        ),
        "adjectives_start": [
            "вспыльчивый(-ая)",
            "невоспитанный(-ая)",
            "осточертевший(-ая) мне",
            "глуповатый(-ая)",
            "надменный(-ая)",
            "неиндивидуалистичный(-ая)",
            "индифферентный(-ая)",
            "недисциплинированный(-ая)",
            "непрофессиональный(-ая)",
            "безответственный(-ая)",
            "безрассудный(-ая)",
            "безразличный(-ая) мне",
        ],
        "nouns": ["участник(-ца) данного чата", "житель(-ница) мира сего"],
        "starts": [
            "Не хочу делать поспешных выводов, но",
            "Я, конечно, не могу утверждать, и это мое субъективное мнение, но",
            (
                "Проанализировав ситуацию, я могу высказать свое субъективное мнение."
                " Оно заключается в том, что"
            ),
            (
                "Не пытаясь никого оскорбить, а лишь высказывая свою скромную точку"
                " зрения, которая не влияет на точку зрения других людей, могу"
                " сказать, что"
            ),
            (
                "Не преследуя попытку затронуть какие-либо социальные меньшинства, хочу"
                " сказать, что"
            ),
        ],
    }

    strings_de = {
        "insult": (
            "<emoji document_id=5373123633415723713>🤬</emoji> {} du bist {} {} {} {}"
        ),
        "adjectives_start": [
            "launisch",
            "hässlich",
            "sinnlos",
            "überheblich",
            "nicht-individualistisch",
            "unordentlich",
            "unprofessionell",
            "unverantwortlich",
            "unvernünftig",
            "uninteressiert",
        ],
        "nouns": ["Teilnehmer dieser Gruppe", "dieser Weltbürger"],
        "starts": [
            (
                "Ich möchte nicht zu voreilig sein und kann nicht behaupten, und"
                " dies ist meine subjektive Meinung, aber"
            ),
            (
                "Nachdem ich die Situation analysiert habe, kann ich meine subjektive"
                " Meinung ausdrücken. Es liegt darin, dass"
            ),
            (
                "Ohne jemanden verletzen zu wollen, sondern nur meine bescheidene"
                " Meinung auszudrücken, die die Meinungen anderer Menschen nicht"
                " beeinflusst, kann ich sagen, dass"
            ),
            (
                "Ohne die Absicht, irgendwelche sozialen Minderheiten zu beeinflussen,"
                " möchte ich sagen, dass"
            ),
        ],
    }

    strings_tr = {
        "insult": (
            "<emoji document_id=5373123633415723713>🤬</emoji> {} sen {} {} {} {}"
        ),
        "adjectives_start": [
            "öfkeli",
            "kaba",
            "gözümü korkutmuş",
            "kibirli",
            "bireysel olmayan",
            "düzensiz",
            "profesyonel olmayan",
            "sorumluluk almamış",
            "akılsız",
            "ilgisiz",
        ],
        "nouns": ["bu sohbet grubunun katılımcısı", "bu dünya vatandaşı"],
        "starts": [
            (
                "Çabucak sonuçlara atlamak istemiyorum ve kesinlikle iddia edemem,"
                " ve bu benim kişisel görüşüm, ama"
            ),
            (
                "Durumu analiz ettiğimde, kişisel görüşümü ifade edebilirim. Bunun"
                " içinde şu var ki"
            ),
            (
                "Herhangi biri duygulanmasını istememekle birlikte, sadece kibarca"
                " bir görüş belirtmek, kişilerin görüşlerinin etkilenmediği, ki"
                " söyleyebilirim ki"
            ),
            (
                "Herhangi bir sosyal azınlığı etkilemek için bir girişimde bulunmadan,"
                " söylemek istediğim şey budur"
            ),
        ],
    }

    strings_hi = {
        "insult": "<emoji document_id=5373123633415723713>🤬</emoji> {} तुम {} {} {} {}",
        "adjectives_start": [
            "अशांत",
            "अज्ञानी",
            "अच्छी तरह से नहीं देखा",
            "अपमानजनक",
            "गैर-व्यक्तिगत",
            "अनुचित",
            "अप्रतिबंधी",
            "अदायगी",
            "असंवेदनशील",
            "अव्यक्तिक",
        ],
        "nouns": ["इस चैट के भागीदार", "इस विश्व नागरिक"],
        "starts": [
            (
                "मैं जल्दी निष्कर्षों को नहीं चाहता हूं और यह कहने से नहीं कि"
                " यह मेरा व्यक्तिगत राय है, लेकिन"
            ),
            "अवस्था का विश्लेषण करके, मैं अपना व्यक्तिगत राय व्यक्त कर सकता हूं। इसमें यह है कि",
            (
                "किसी को दुखाने की कोशिश न करते हुए, केवल मेरा बहुत छोटा राय"
                " बताना, लोगों की रायों को प्रभावित न करने के लिए, जो"
                " मैं कह सकता हूं कि"
            ),
            "किसी सामाजिक अनुकूलित समूह को प्रभावित न करने के लिए, मैं कहना चाहता हूं कि",
        ],
    }

    async def insultocmd(self, message: Message):
        """Use when angry"""
        await utils.answer(
            message,
            self.strings("insult").format(
                random.choice(self.strings("starts")),
                random.choice(self.strings("adjectives_start")),
                random.choice(self.strings("adjectives_start")),
                random.choice(self.strings("nouns")),
                random.choice(["!!!!", "!", "."]),
            ),
        )
