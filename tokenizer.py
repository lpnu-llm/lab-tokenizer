# %% [markdown]
# # Токенізація
#
# Мовна модель працює не з текстом, а з послідовністю чисел. Тому перед входом
# у трансформер текст проходить важливе перетворення:
#
# 1. **токенізатор** ділить текст на токени та замінює їх ідентифікаторами;
#
# У цій лабораторній ми пройдемо шлях від токенів-слів до BPE і WordPiece,
# а потім побачимо, чому самих токенів недостатньо для трансформера. Усі алгоритми
# реалізуємо з нуля, використовуючи лише стандартну бібліотеку Python.

# %% [markdown]
# ## 1. Токенізатор на рівні слів
#
# Найпростіша ідея — вважати кожне слово окремим токеном. Спочатку приведемо
# текст до нижнього регістру, відділимо розділові знаки й збережемо український
# апостроф усередині слова.
#
# ```python
# word_tokenize("Комп'ютер навчається!")
# # ["комп'ютер", "навчається", "!"]
# ```
#
# Така нормалізація зменшує словник: `Модель` і `модель` стають одним токеном.
# Водночас ми втрачаємо частину інформації. У реальних токенізаторах правила
# нормалізації є окремим важливим рішенням.

# %%

def word_tokenize(text):
    """Ділить текст на слова, числа й розділові знаки."""

    # Підказка: модуль re підтримує Unicode. Апострофи ' та ’ можуть бути
    # частиною слова, але крапка або кома мають стати окремими токенами.
    raise NotImplementedError()


def test_word_tokenize():
    assert word_tokenize("Модель читає текст.") == [
        "модель", "читає", "текст", "."
    ]
    assert word_tokenize("Комп'ютер і пам’ять") == [
        "комп'ютер", "і", "пам’ять"
    ]
    assert word_tokenize("GPT-2: 50 токенів!") == [
        "gpt", "-", "2", ":", "50", "токенів", "!"
    ]
    assert word_tokenize("") == []


if __name__ == "__main__":
    test_word_tokenize()
    print("✓ word_tokenize")

# %% [markdown]
# ### Словник та проблема OOV
#
# Побудуємо словник тільки за навчальним корпусом. Два спеціальні токени:
#
# - `<pad>` доповнює послідовності до однакової довжини;
# - `<unk>` замінює невідоме слово (**out of vocabulary**, OOV).
#
# Якщо модель бачила `кіт`, але не бачила `котик`, усе слово `котик` стане
# `<unk>`. Різні невідомі слова отримають однаковий id — їх уже неможливо
# відрізнити.

# %%

def build_word_vocab(texts) -> dict[str, int]:
    """Будує словник token -> id; звичайні токени сортує за абеткою."""

    # <pad> повинен мати id 0, а <unk> — id 1.
    raise NotImplementedError()


def encode_words(text, vocab):
    """Перетворює текст на список id, використовуючи <unk> для OOV."""

    raise NotImplementedError()


def test_word_vocab():
    vocab = build_word_vocab(["Кіт спить.", "Пес спить."])
    assert vocab["<pad>"] == 0
    assert vocab["<unk>"] == 1
    assert encode_words("Кіт біжить.", vocab) == [vocab["кіт"], 1, vocab["."]]
    assert encode_words("Хом'як біжить.", vocab)[0:2] == [1, 1]


if __name__ == "__main__":
    test_word_vocab()
    print("✓ word vocabulary")

# Питання:
# - Що станеться зі словником, якщо не привести слова до нижнього регістру?
# - Чому великий словник збільшує кількість параметрів embedding-таблиці?
# - Яку інформацію втрачено у двох послідовностях `[1, 1, id_крапки]`?

# %% [markdown]
# ## 2. Символьні n-грами
#
# Замість цілого слова можна взяти всі послідовності з `n` сусідніх символів.
# Додамо маркери `^` і `$`, щоб відрізняти початок та кінець слова:
#
# ```python
# char_ngrams("кіт", 3) == ["^кі", "кіт", "іт$"]
# ```
#
# У споріднених слів є спільні частини. Наприклад, навіть якщо `токенізація`
# не траплялася в корпусі, її триграми можуть перетинатися з триграмами слова
# `токенізатор`. Отже, замість одного беззмістовного `<unk>` ми отримуємо
# часткову інформацію про невідоме слово.

# %%

def char_ngrams(word, n=3):
    """Повертає символьні n-грами слова з маркерами меж ^ та $."""

    raise NotImplementedError()


def ngram_overlap(word_a, word_b, n=3):
    """Частка спільних n-грам за коефіцієнтом Жаккара."""

    # |A ∩ B| / |A ∪ B|. Для двох порожніх множин поверніть 1.0.
    raise NotImplementedError()


def test_ngrams():
    assert char_ngrams("кіт", 3) == ["^кі", "кіт", "іт$"]
    assert char_ngrams("кіт", 2) == ["^к", "кі", "іт", "т$"]
    assert char_ngrams("", 3) == []
    assert ngram_overlap("токенізатор", "токенізація", 3) > 0.4
    assert ngram_overlap("кіт", "трактор", 3) == 0.0

    try:
        char_ngrams("слово", 0)
    except ValueError:
        pass
    else:
        raise AssertionError("n має бути додатним")


if __name__ == "__main__":
    test_ngrams()
    print("✓ character n-grams")

# Питання:
# - Які переваги й недоліки матимуть біграми порівняно з п'ятиграмами?
# - Чи зникає OOV повністю, якщо алфавіт під час інференсу теж може змінитися?
# - Чому набір n-грам добре показує схожість, але не зберігає їх порядок?

# %% [markdown]
# ## 3. Byte Pair Encoding (BPE)
#
# Символьна токенізація не має OOV для знайомого алфавіту, але створює довгі
# послідовності. Токенізація словами дає короткі послідовності, але величезний
# словник та OOV. **BPE** шукає компроміс:
#
# 1. починаємо з окремих символів;
# 2. рахуємо частоти всіх сусідніх пар у корпусі;
# 3. найчастішу пару об'єднуємо в один токен;
# 4. повторюємо задану кількість разів.
#
# Часті фрагменти стають одним токеном, а рідкі слова все одно можна скласти з
# менших частин. Маркер `</w>` позначає кінець слова й не дає зливати символи
# з різних слів.

# %%

def word_frequencies(texts):
    """Рахує частоти слів у корпусі, ігноруючи пунктуацію та числа."""

    raise NotImplementedError()


def most_frequent_pair(vocabulary):
    """Знаходить найчастішу сусідню пару у зваженому BPE-словнику."""

    # vocabulary має вигляд {("м", "а", "м", "а", "</w>"): 2, ...}.
    # За однакової частоти виберіть лексикографічно найменшу пару.
    raise NotImplementedError()


def merge_pair(symbols, pair):
    """Зливає всі неперекривні входження pair у послідовності symbols."""

    raise NotImplementedError()


def train_bpe(texts, num_merges):
    """Навчає BPE та повертає список злиттів у порядку застосування."""

    # Навчання тут означає лише підрахунок частот, а не gradient descent.
    raise NotImplementedError()



def apply_bpe(word, merges):
    """Токенізує одне слово, послідовно застосовуючи вивчені злиття."""

    raise NotImplementedError()


def test_bpe():
    vocabulary = {
        ("м", "а", "м", "а", "</w>"): 2,
        ("м", "а", "л", "а", "</w>"): 1,
    }
    assert most_frequent_pair(vocabulary) == ("м", "а")
    assert merge_pair(("м", "а", "м", "а", "</w>"), ("м", "а")) == (
        "ма", "ма", "</w>"
    )

    # Усі символи слова "мамонт" є в train-корпусі, але самого слова немає.
    merges = train_bpe(["мама мама мала тон"], 3)
    assert merges[0] == ("м", "а")
    assert apply_bpe("мама", merges) == ["мама</w>"]

    # Незнайоме слово теж розкладається: воно не стає одним <unk>.
    unseen = apply_bpe("мамонт", merges)
    assert "<unk>" not in unseen
    assert "".join(unseen).replace("</w>", "") == "мамонт"


if __name__ == "__main__":
    test_bpe()
    print("✓ BPE")

# %% [markdown]
# ### Чи справді BPE скорочує послідовності?
#
# Перевіримо це вимірюванням, а не припущенням. До навчання одне слово має
# приблизно стільки токенів, скільки в ньому символів. Після кожного злиття
# деякі часті пари займають одну позицію замість двох.
#
# Важливо: більше злиттів зазвичай означає коротші послідовності, але більший
# словник. BPE не гарантує, що кожне окреме слово стане коротшим, особливо якщо
# воно не схоже на навчальний корпус.

# %%

def average_bpe_length(texts, merges):
    """Середня кількість BPE-токенів на слово у корпусі."""

    raise NotImplementedError()


def test_average_bpe_length():
    corpus = [
        "токен токени токенізація",
        "токенізатор токенізує текст",
    ]
    merges = train_bpe(corpus, 20)
    before = average_bpe_length(corpus, [])
    after = average_bpe_length(corpus, merges)
    assert after < before
    assert before > 1


if __name__ == "__main__":
    test_average_bpe_length()
    print("✓ BPE reduces average sequence length")

# Питання:
# - Що ми отримуємо ціною збільшення словника BPE?
# - Чому коректніше порівнювати довжину на окремому test-корпусі?
# - Звичайний BPE починається із символів. Як byte-level BPE уникає OOV навіть
#   для емодзі, нового алфавіту або рідкісного Unicode-символу?

# %% [markdown]
# ## 4. WordPiece
#
# WordPiece навчається майже як BPE: починає із символів і поступово зливає
# сусідні фрагменти. Значну частину логіки можна адаптувати з попереднього завдання.
#
# Відмінності: `##` позначає продовження слова; пари вибираються за оцінкою,
# а не лише за частотою; під час токенізації шукають найдовший фрагмент зі словника.
#
# `score(a, b) = frequency(a, b) / (frequency(a) * frequency(b))`

# %%


def wordpiece_symbols(word):
    """Розбиває слово на початкові WordPiece-символи з префіксом ##."""

    # Перший символ починає слово, решта — його продовження.
    raise NotImplementedError()


def wordpiece_pair_scores(vocabulary):
    """Обчислює WordPiece-score сусідніх пар у зваженому словнику."""

    # Порахуйте зважені частоти фрагментів і сусідніх пар для формули вище.
    raise NotImplementedError()


def merge_wordpiece_pair(symbols, pair):
    """Зливає пару, зберігаючи ##, якщо результат не починає слово."""

    # Як у BPE, але `##` має позначати позицію, а не дублюватися при злитті.
    raise NotImplementedError()


def train_wordpiece(texts, vocab_size):
    """Навчає WordPiece-словник заданого максимального розміру."""

    # За однакового score вибираємо лексикографічно найменшу пару.
    raise NotImplementedError()


def apply_wordpiece(word, vocab, unk_token="[UNK]"):
    """Токенізує слово жадібним longest-match-first алгоритмом BERT."""

    # На кожній позиції шукайте найдовший фрагмент зі словника.
    # Якщо розкласти слово повністю не вдається, поверніть `[UNK]`.
    raise NotImplementedError()


def test_wordpiece():
    weighted_vocab = {
        ("а", "##б"): 2,
        ("а", "##в"): 1,
        ("г", "##в"): 2,
    }
    scores = wordpiece_pair_scores(weighted_vocab)
    assert scores[("а", "##б")] > scores[("а", "##в")]
    assert merge_wordpiece_pair(("м", "##а", "##м", "##а"), ("м", "##а")) == (
        "ма", "##м", "##а"
    )

    vocab = train_wordpiece(["мама мама мала тон"], 30)
    assert "[UNK]" in vocab
    assert apply_wordpiece("мама", vocab) == ["мама"]

    # На відміну від BPE, WordPiece шукає найдовший фрагмент зі словника,
    # а не повторює послідовність вивчених злиттів.
    bert_vocab = {"[UNK]", "ток", "токен", "##ен", "##ізація"}
    assert apply_wordpiece("токенізація", bert_vocab) == ["токен", "##ізація"]
    assert apply_wordpiece("токенx", bert_vocab) == ["[UNK]"]
    assert apply_wordpiece("", bert_vocab) == []

    try:
        train_wordpiece(["текст"], 0)
    except ValueError:
        pass
    else:
        raise AssertionError("vocab_size має бути додатним")


if __name__ == "__main__":
    test_wordpiece()
    print("✓ WordPiece")

# Питання:
# - Чому `##` потрібен, щоб відрізняти початок слова від його продовження?
# - Чим WordPiece-score відрізняється від вибору найчастішої пари у BPE?
# - Чому BERT повертає `[UNK]` для цілого слова, якщо не знаходить один фрагмент?

# %% [markdown]
# ## 5. Великий експеримент: FLORES та GPT
#
# Тепер застосуємо вивчені ідеї до справжнього багатомовного корпусу. Навчимо
# власні токенізатори на англійській, українській та грузинській мовах, а потім
# порівняємо їх із готовими токенізаторами GPT.
#
# Використаємо `dev` split FLORES-200: по 997 паралельних речень кожною мовою,
# тобто 2991 навчальний рядок. Це небагато для реальної мовної моделі, але
# достатньо для навчального експерименту з токенізацією.
#
# Код завантаження даних уже готовий. Його реалізовувати не потрібно.

# %%

from datasets import load_dataset


FLORES_LANGUAGES = {
    "English": "eng_Latn",
    "Українська": "ukr_Cyrl",
    "ქართული": "kat_Geor",
}


def load_flores_dev():
    """Завантажує по 997 речень FLORES для кожної вибраної мови."""
    corpora = {}
    for language, config in FLORES_LANGUAGES.items():
        dataset = load_dataset(
            "tomasmajercik/flores-parquet",
            config,
            split="validation",
        )
        corpora[language] = list(dataset["sentence"])
    return corpora


flores = load_flores_dev()

assert all(len(texts) == 997 for texts in flores.values())
train_texts = [
    text
    for language_texts in flores.values()
    for text in language_texts
]

print({language: len(texts) for language, texts in flores.items()})
print("Усього навчальних рядків:", len(train_texts))

# %% [markdown]
# Подивіться на одне й те саме речення трьома мовами. FLORES є паралельним
# корпусом, тому рядки з однаковим індексом мають однаковий зміст.

# %%

example_index = 0
for language, texts in flores.items():
    print(f"{language}: {texts[example_index]}\n")

# Питання:
# - Чому для порівняння важливо мати однакову кількість текстів кожною мовою?
# - Чи є 997 речень репрезентативними для всього різноманіття мови?

# %% [markdown]
# ### Навчання на FLORES із різними словниками
#
# Тут не створюємо нових алгоритмів. Повторно використайте вже реалізовані
# `train_bpe`, `apply_bpe`, `train_wordpiece` та `apply_wordpiece`.
#
# Навчіть обидва токенізатори зі словниками приблизно 500, 1000 і 2000 токенів.
# Для BPE початковий словник уже містить символи, а кожне merge додає один
# токен, тому бажаний розмір словника треба перетворити на кількість merges.

# %%

VOCAB_SIZES = (500, 1000, 2000)


def bpe_num_merges(texts, vocab_size):
    """Обчислює кількість BPE-merges для бажаного розміру словника."""
    frequencies = word_frequencies(texts)
    characters = {
        character
        for word in frequencies
        for character in word
    }
    initial_vocab_size = len(characters) + 1  # </w>
    if vocab_size < initial_vocab_size:
        raise ValueError("vocab_size менший за початковий алфавіт")
    return vocab_size - initial_vocab_size


def apply_bpe_to_text(text, merges):
    """Застосовує створений раніше BPE до всіх токенів тексту."""
    return [
        piece
        for token in word_tokenize(text)
        for piece in apply_bpe(token, merges)
    ]


def apply_wordpiece_to_text(text, vocab):
    """Застосовує створений раніше WordPiece до всіх токенів тексту."""
    return [
        piece
        for token in word_tokenize(text)
        for piece in apply_wordpiece(token, vocab)
    ]


bpe_models = {}
wordpiece_models = {}

for vocab_size in VOCAB_SIZES:
    bpe_models[vocab_size] = train_bpe(
        train_texts,
        bpe_num_merges(train_texts, vocab_size),
    )
    wordpiece_models[vocab_size] = train_wordpiece(
        train_texts,
        vocab_size,
    )

print("Навчено BPE і WordPiece для:", VOCAB_SIZES)

# Питання:
# - Як змінюється час навчання зі збільшенням словника?
# - Чи розподіляються токени порівну між трьома системами письма?
# - Чи завжди більший словник дає нижчу fertility?

# %% [markdown]
# ### Готові GPT-токенізатори
#
# Наступний код уже готовий. `tiktoken` імпортує ті самі encoding-и, які
# використовують відповідні покоління GPT. GPT-3.5 і класичний GPT-4 мають
# однаковий `cl100k_base`, тому їхні результати збігатимуться.

# %%

import tiktoken


gpt_encodings = {
    "GPT-2": tiktoken.encoding_for_model("gpt-2"),
    "GPT-3.5": tiktoken.encoding_for_model("gpt-3.5-turbo"),
    "GPT-4": tiktoken.encoding_for_model("gpt-4"),
    "GPT-5": tiktoken.encoding_for_model("gpt-5"),
}

for name, encoding in gpt_encodings.items():
    print(f"{name:7} -> {encoding.name:12} ({encoding.n_vocab} tokens)")

# %% [markdown]
# ### Fertility
#
# **Fertility** — середня кількість токенів на одне слово:
#
# $$\text{fertility} =
# \frac{\text{загальна кількість токенів}}
#      {\text{загальна кількість слів}}$$
#
# У цій лабораторній словом вважаємо непорожній фрагмент після `str.split()`.
# Рахуйте відношення двох сум для всього корпусу, а не середнє значень окремих
# речень: тоді кожне слово має однакову вагу.

# %%

def fertility(tokenize, texts):
    """Повертає середню кількість токенів на whitespace-separated слово."""
    raise NotImplementedError()


def test_fertility():
    assert fertility(list, ["aa b", "ccc"]) == 7 / 3

    try:
        fertility(list, ["", "   "])
    except ValueError:
        pass
    else:
        raise AssertionError("Корпус без слів має давати ValueError")


if __name__ == "__main__":
    test_fertility()
    print("✓ fertility")

# %% [markdown]
# ### Порівняння за мовами
#
# Побудуйте таблицю fertility для всіх 10 токенізаторів:
#
# - BPE: 500, 1000, 2000;
# - WordPiece: 500, 1000, 2000;
# - GPT-2, GPT-3.5, GPT-4, GPT-5.
#
# Наші моделі перевіряються на тому самому `dev`, на якому навчалися. Отже, це
# train fertility — вона показує стиснення корпусу, але не узагальнення.

# %%

if __name__ == "__main__":
    tokenizers_to_compare = {}

    for vocab_size, merges in bpe_models.items():
        tokenizers_to_compare[f"BPE-{vocab_size}"] = (
            lambda text, merges=merges: apply_bpe_to_text(text, merges)
        )

    for vocab_size, vocab in wordpiece_models.items():
        tokenizers_to_compare[f"WordPiece-{vocab_size}"] = (
            lambda text, vocab=vocab: apply_wordpiece_to_text(text, vocab)
        )

    for name, encoding in gpt_encodings.items():
        tokenizers_to_compare[name] = encoding.encode


    def fertility_table(tokenizers, corpora):
        """Обчислює вкладений dict tokenizer -> language -> fertility."""
        raise NotImplementedError()


    results = fertility_table(tokenizers_to_compare, flores)

    header = f"{'tokenizer':<24}" + "".join(
        f"{language:>14}" for language in flores
    )
    print(header)
    print("-" * len(header))
    for tokenizer_name, language_values in results.items():
        row = f"{tokenizer_name:<24}" + "".join(
            f"{language_values[language]:14.3f}" for language in flores
        )
        print(row)

# Питання:
# - Для якої мови GPT-2 має найбільшу fertility? Чому?
# - Як змінюється fertility при переході 500 → 1000 → 2000?
# - Чому GPT-токенізатор із великим словником може програти маленькому
#   токенізатору, навченому саме на цих трьох мовах?

# %% [markdown]
# ### Змішані та складні випадки
#
# Середня fertility приховує конкретні невдалі розбиття. Порівняйте кількість
# та самі токени для code-switching, різних систем письма, чисел, emoji, URL і
# слів, яких не було у FLORES.

# %%

MIXED_CASES = [
    "Я навчаю tokenizer на FLORES dataset.",
    "The model розуміє ქართულ ენას?",
    "Київ -> Tbilisi -> თბილისი -> London 🌍",
    "Замовлення №2026-09-24 коштує $19.99.",
    "support@example.com або https://example.com/допомога",
    "я дуже втомився від курсу основи Large Language Models"
]


def compare_mixed_cases(texts, tokenizers):
    """Друкує кількість токенів кожного tokenizer для кожного тексту."""
    raise NotImplementedError()


if __name__ == "__main__":
    compare_mixed_cases(MIXED_CASES, tokenizers_to_compare)

# Фінальні питання:
# - Які символи або фрагменти стабільно створюють найбільше токенів?
# - Який tokenizer найкраще поводиться, коли в одному реченні три мови?
# - Чому fertility недостатньо для остаточного вибору токенізатора?
