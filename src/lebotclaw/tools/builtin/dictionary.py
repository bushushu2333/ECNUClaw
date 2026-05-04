from lebotclaw.tools.base import Tool, ToolResult

_DICTIONARY = {
    "zh": {
        "苹果": {
            "pinyin": "píng guǒ",
            "pos": "名词",
            "definition": "一种常见的水果，圆形，红色或绿色，味甜或略酸。",
            "example": "我每天早上都会吃一个苹果。",
            "english": "apple",
        },
        "学习": {
            "pinyin": "xué xí",
            "pos": "动词",
            "definition": "通过阅读、听讲、研究、实践等获得知识和技能。",
            "example": "同学们在学校里认真学习。",
            "english": "study / learn",
        },
        "美丽": {
            "pinyin": "měi lì",
            "pos": "形容词",
            "definition": "好看，漂亮，使人看了产生快感的。",
            "example": "秋天的景色非常美丽。",
            "english": "beautiful",
        },
        "朋友": {
            "pinyin": "péng you",
            "pos": "名词",
            "definition": "彼此有交情、感情好的人。",
            "example": "我和小明是好朋友。",
            "english": "friend",
        },
        "勇敢": {
            "pinyin": "yǒng gǎn",
            "pos": "形容词",
            "definition": "不怕危险和困难，有胆量。",
            "example": "消防员叔叔非常勇敢。",
            "english": "brave",
        },
        "学校": {
            "pinyin": "xué xiào",
            "pos": "名词",
            "definition": "专门进行教育的机构。",
            "example": "我们的学校很大很漂亮。",
            "english": "school",
        },
        "快乐": {
            "pinyin": "kuài lè",
            "pos": "形容词",
            "definition": "感到幸福或满意。",
            "example": "祝大家新年快乐！",
            "english": "happy",
        },
        "读书": {
            "pinyin": "dú shū",
            "pos": "动词",
            "definition": "看着书本文字并理解其意义；也指上学学习。",
            "example": "我每天晚上都会读书半小时。",
            "english": "read books / study",
        },
        "太阳": {
            "pinyin": "tài yáng",
            "pos": "名词",
            "definition": "太阳系的中心天体，发光发热的恒星。",
            "example": "太阳从东方升起，从西方落下。",
            "english": "sun",
        },
        "帮助": {
            "pinyin": "bāng zhù",
            "pos": "动词",
            "definition": "替人出力、出主意或给以物质上的支援。",
            "example": "他经常帮助同学解决问题。",
            "english": "help / assist",
        },
    },
    "en": {
        "apple": {
            "pos": "noun",
            "definition": "A round fruit with red, green, or yellow skin and white flesh.",
            "example": "An apple a day keeps the doctor away.",
            "chinese": "苹果",
            "phonetic": "/ˈæp.əl/",
        },
        "study": {
            "pos": "verb / noun",
            "definition": "To spend time learning about a subject, especially by reading.",
            "example": "She studies English every evening.",
            "chinese": "学习",
            "phonetic": "/ˈstʌd.i/",
        },
        "beautiful": {
            "pos": "adjective",
            "definition": "Very attractive and pleasing to look at.",
            "example": "What a beautiful sunset!",
            "chinese": "美丽的",
            "phonetic": "/ˈbjuː.tɪ.fəl/",
        },
        "friend": {
            "pos": "noun",
            "definition": "A person you know well and like, who is not a family member.",
            "example": "Tom is my best friend.",
            "chinese": "朋友",
            "phonetic": "/frend/",
        },
        "brave": {
            "pos": "adjective",
            "definition": "Showing no fear of dangerous or difficult things.",
            "example": "The brave soldier saved many lives.",
            "chinese": "勇敢的",
            "phonetic": "/breɪv/",
        },
        "school": {
            "pos": "noun",
            "definition": "A place where children go to learn.",
            "example": "I walk to school every morning.",
            "chinese": "学校",
            "phonetic": "/skuːl/",
        },
        "happy": {
            "pos": "adjective",
            "definition": "Feeling pleasure and enjoyment because of your life or situation.",
            "example": "I am happy to see you!",
            "chinese": "快乐的",
            "phonetic": "/ˈhæp.i/",
        },
        "book": {
            "pos": "noun",
            "definition": "A set of printed pages fastened together inside a cover.",
            "example": "I'm reading an interesting book.",
            "chinese": "书",
            "phonetic": "/bʊk/",
        },
        "sun": {
            "pos": "noun",
            "definition": "The star that the Earth moves around and that gives light and heat.",
            "example": "The sun was shining brightly today.",
            "chinese": "太阳",
            "phonetic": "/sʌn/",
        },
        "help": {
            "pos": "verb / noun",
            "definition": "To make it possible or easier for someone to do something.",
            "example": "Can you help me with my homework?",
            "chinese": "帮助",
            "phonetic": "/help/",
        },
        "water": {
            "pos": "noun",
            "definition": "A clear liquid that falls from the sky as rain and is in rivers and lakes.",
            "example": "Please drink more water when it's hot.",
            "chinese": "水",
            "phonetic": "/ˈwɔː.tər/",
        },
        "animal": {
            "pos": "noun",
            "definition": "A living creature that is not a plant or human.",
            "example": "Lions are strong animals.",
            "chinese": "动物",
            "phonetic": "/ˈæn.ɪ.məl/",
        },
    },
}


class DictionaryTool(Tool):
    name = "dictionary"
    description = "Chinese-English dictionary lookup. Returns definition, pinyin/phonetic, part of speech, example sentence, and translation."
    parameters = {
        "type": "object",
        "properties": {
            "word": {
                "type": "string",
                "description": "The word to look up.",
            },
            "language": {
                "type": "string",
                "enum": ["zh", "en"],
                "description": "Language of the input word: 'zh' for Chinese, 'en' for English. Defaults to 'zh'.",
            },
        },
        "required": ["word"],
    }

    def execute(self, **kwargs) -> ToolResult:
        word = kwargs.get("word", "").strip()
        language = kwargs.get("language", "zh").strip()

        if not word:
            return ToolResult(success=False, output="", error="No word provided")

        if language not in _DICTIONARY:
            return ToolResult(
                success=False, output="",
                error=f"Unsupported language '{language}'. Use 'zh' or 'en'.",
            )

        entry = _DICTIONARY[language].get(word)
        if entry is None:
            other_lang = "en" if language == "zh" else "zh"
            for lang_key, lang_data in _DICTIONARY.items():
                if lang_key == language:
                    continue
                for w, info in lang_data.items():
                    cross_key = "english" if lang_key == "zh" else "chinese"
                    if cross_key in info and word.lower() in info[cross_key].lower().split("/"):
                        entry = _DICTIONARY[language].get(w) or _DICTIONARY[lang_key].get(w)
                        if entry:
                            word = w
                            language = lang_key
                            break
                if entry:
                    break

        if entry is None:
            available = ", ".join(sorted(_DICTIONARY[language].keys()))
            return ToolResult(
                success=False, output="",
                error=f"Word '{word}' not found in {language} dictionary. Available: {available}",
                metadata={"available_words": list(_DICTIONARY[language].keys())},
            )

        lines = [f"【{word}】"]
        if "pinyin" in entry:
            lines.append(f"拼音: {entry['pinyin']}")
        if "phonetic" in entry:
            lines.append(f"Phonetic: {entry['phonetic']}")
        lines.append(f"词性: {entry['pos']}")
        lines.append(f"释义: {entry['definition']}")
        lines.append(f"例句: {entry['example']}")
        if "english" in entry:
            lines.append(f"英文: {entry['english']}")
        if "chinese" in entry:
            lines.append(f"中文: {entry['chinese']}")

        return ToolResult(
            success=True,
            output="\n".join(lines),
            metadata={"word": word, "language": language, **entry},
        )
