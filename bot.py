#!/usr/bin/env python3
"""Простой FAQ-бот для терминала: ищет ответ по совпадению ключевых слов."""

import os
import re
import sys

FAQ_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faq.txt")

MIN_WORD_LEN = 3
STOPWORDS = {
    "что", "как", "где", "кто", "это", "или", "для", "при", "про", "над", "под",
    "так", "уже", "еще", "ещё", "там", "тут", "они", "оно", "она", "мне", "меня",
    "нам", "вам", "нас", "вас", "его", "ему", "них", "ним", "все", "всё", "весь",
    "быть", "есть", "буду", "будет", "надо", "нужно", "можно", "если", "чтобы",
    "какой", "какая", "какие", "каких", "какое", "каком", "ваш", "ваша", "мой",
    "там", "потом", "тоже", "очень", "более", "менее", "куда", "когда",
    "откуда", "почему", "зачем", "чего", "кого", "кому", "чем", "нам",
}
# Вес слов из ответа: они помогают, но вопрос важнее.
ANSWER_WEIGHT = 0.8
# Русская морфология: слова сравниваем по общему началу, а не целиком.
STEM_LONG = 4
STEM_LONG_SCORE = 0.8
STEM_SHORT = 3
STEM_SHORT_SCORE = 0.55
THRESHOLD = 0.3

PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


def normalize(text):
    """Нижний регистр, без пунктуации, только значимые слова."""
    text = text.lower().replace("ё", "е")
    text = PUNCT_RE.sub(" ", text)
    words = []
    for word in text.split():
        if len(word) < MIN_WORD_LEN or word in STOPWORDS:
            continue
        words.append(word)
    return words


def load_faq(path):
    """Читает faq.txt в список записей с готовыми ключевыми словами."""
    entries = []
    question = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line.startswith("Q:"):
                question = line[2:].strip()
            elif line.startswith("A:") and question is not None:
                answer = line[2:].strip()
                keywords = {}
                for word in normalize(answer):
                    keywords[word] = ANSWER_WEIGHT
                for word in normalize(question):
                    keywords[word] = 1.0
                entries.append({"question": question, "answer": answer, "keywords": keywords})
                question = None
    if not entries:
        raise ValueError("В faq.txt не найдено ни одной пары Q/A")
    return entries


def common_prefix(first, second):
    """Длина общего начала двух слов."""
    size = 0
    for left, right in zip(first, second):
        if left != right:
            break
        size += 1
    return size


def match_word(word, keywords):
    """Точное совпадение — полный вес, похожее по корню слово — неполный."""
    if word in keywords:
        return keywords[word]
    best = 0.0
    for key, weight in keywords.items():
        shared = common_prefix(word, key)
        if shared >= STEM_LONG:
            best = max(best, weight * STEM_LONG_SCORE)
        elif shared >= STEM_SHORT and len(word) >= 5 and len(key) >= 5:
            best = max(best, weight * STEM_SHORT_SCORE)
    return best


def score(words, entry):
    """Доля ключевых слов вопроса, найденных в записи FAQ."""
    if not words:
        return 0.0
    total = sum(match_word(word, entry["keywords"]) for word in words)
    return min(total / len(words), 1.0)


def find_answer(question, entries):
    words = normalize(question)
    best_entry, best_score = None, 0.0
    for entry in entries:
        value = score(words, entry)
        if value > best_score:
            best_entry, best_score = entry, value
    if best_entry is None or best_score < THRESHOLD:
        return None, best_score
    return best_entry, best_score


def main():
    try:
        entries = load_faq(FAQ_PATH)
    except (OSError, ValueError) as err:
        print("Не смог прочитать faq.txt: %s" % err, file=sys.stderr)
        return 1

    print("FAQ-бот репетиции. Задайте вопрос, выход — exit или Ctrl+C.")
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question.lower() in ("exit", "quit", "выход"):
            break
        entry, value = find_answer(question, entries)
        if entry is None:
            print("не знаю")
        else:
            print(entry["answer"])
    print("Пока!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
