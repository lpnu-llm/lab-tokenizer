# %% [markdown]
# # Токенізація та позиційне кодування
#
# Мовна модель працює не з текстом, а з послідовністю чисел. Тому перед входом
# у трансформер текст проходить два важливі перетворення:
#
# 1. **токенізатор** ділить текст на токени та замінює їх ідентифікаторами;
# 2. **позиційне кодування** додає інформацію про порядок токенів.
#
# У цій лабораторній ми пройдемо шлях від токенів-слів до BPE, а потім
# побачимо, чому самих токенів недостатньо для трансформера. Усі алгоритми
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
    ...


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

def build_word_vocab(texts):
    """Будує словник token -> id; звичайні токени сортує за абеткою."""

    # <pad> повинен мати id 0, а <unk> — id 1.
    ...


def encode_words(text, vocab):
    """Перетворює текст на список id, використовуючи <unk> для OOV."""

    ...


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

    ...


def ngram_overlap(word_a, word_b, n=3):
    """Частка спільних n-грам за коефіцієнтом Жаккара."""

    # |A ∩ B| / |A ∪ B|. Для двох порожніх множин поверніть 1.0.
    ...


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

    ...


def most_frequent_pair(vocabulary):
    """Знаходить найчастішу сусідню пару у зваженому BPE-словнику."""

    # vocabulary має вигляд {("м", "а", "м", "а", "</w>"): 2, ...}.
    # За однакової частоти виберіть лексикографічно найменшу пару.
    ...


def merge_pair(symbols, pair):
    """Зливає всі неперекривні входження pair у послідовності symbols."""

    ...


def train_bpe(texts, num_merges):
    """Навчає BPE та повертає список злиттів у порядку застосування."""

    # Навчання тут означає лише підрахунок частот, а не gradient descent.
    ...


def apply_bpe(word, merges):
    """Токенізує одне слово, послідовно застосовуючи вивчені злиття."""

    ...


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

    ...


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
# - Що ми купуємо ціною збільшення словника BPE?
# - Чому коректніше порівнювати довжину на окремому test-корпусі?
# - Звичайний BPE починається із символів. Як byte-level BPE уникає OOV навіть
#   для емодзі, нового алфавіту або рідкісного Unicode-символу?

# %% [markdown]
# ## 4. Навіщо потрібна інформація про позицію
#
# Після токенізації кожен id замінюється embedding-вектором. Але той самий
# токен у різних місцях має той самий embedding. Ба більше, self-attention без
# позиційної інформації не знає, який токен був першим, а який другим.
#
# Порівняйте речення:
#
# - `пес вкусив чоловіка`;
# - `чоловік вкусив пса`.
#
# Набір слів майже той самий, але порядок змінює зміст. Тому до embedding
# токена додають вектор його позиції:
#
# $$x_p = e_{token} + p_p$$
#
# Розмірності обох векторів мають збігатися. Додавання, а не конкатенація,
# зберігає розмір `d_model`.

# %%

def add_position(token_embeddings, position_embeddings):
    """Поелементно додає позиційні вектори до embedding-векторів токенів."""

    ...


def test_add_position():
    # Два однакові токени спочатку мають однакові представлення.
    tokens = [[1.0, 2.0], [1.0, 2.0]]
    positions = [[0.0, 0.0], [0.5, -0.5]]
    result = add_position(tokens, positions)
    assert result == [[1.0, 2.0], [1.5, 1.5]]
    assert result[0] != result[1]

    try:
        add_position([[1.0, 2.0]], [[1.0]])
    except ValueError:
        pass
    else:
        raise AssertionError("Розмірності embedding-векторів мають збігатися")


if __name__ == "__main__":
    test_add_position()
    print("✓ add_position")

# %% [markdown]
# ## 5. Синусоїдальне позиційне кодування
#
# В оригінальному Transformer позиційні вектори не навчалися. Для позиції
# `pos` і парного `d_model` їх обчислювали так:
#
# $$PE(pos, 2i) = \sin\left(pos / 10000^{2i/d_{model}}\right)$$
#
# $$PE(pos, 2i+1) = \cos\left(pos / 10000^{2i/d_{model}}\right)$$
#
# Кожна пара координат коливається з іншою частотою: швидкі хвилі добре
# розрізняють сусідні позиції, повільні — далекі. Кодування детерміноване, не
# додає параметрів і його можна обчислити для довжини, якої не було в train.

# %%

def sinusoidal_encoding(length, d_model):
    """Створює матрицю PE форми (length, d_model)."""

    # Використайте sin і cos з модуля math. Вимагайте парний d_model.
    ...


def test_sinusoidal_encoding():
    from math import isclose

    pe = sinusoidal_encoding(4, 6)
    assert len(pe) == 4
    assert all(len(row) == 6 for row in pe)
    assert pe[0] == [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    assert isclose(pe[1][0], 0.8414709848, rel_tol=1e-9)
    assert isclose(pe[1][1], 0.5403023059, rel_tol=1e-9)
    assert pe[1] != pe[2]

    try:
        sinusoidal_encoding(3, 5)
    except ValueError:
        pass
    else:
        raise AssertionError("Для цієї реалізації d_model має бути парним")


if __name__ == "__main__":
    test_sinusoidal_encoding()
    print("✓ sinusoidal encoding")

# %% [markdown]
# ## 6. Навчені позиційні embedding-и
#
# Інший підхід — створити таблицю `max_length × d_model`. Рядок з індексом
# `pos` є звичайним параметром моделі й оновлюється під час тренування разом з
# іншими вагами. У цій лабораторній ми не тренуємо модель: функція лише вибере
# потрібні рядки з уже заданої таблиці.
#
# Перевага — модель сама знаходить корисне кодування позицій. Недоліки —
# додаткові параметри та фіксована максимальна довжина. Для позиції поза
# таблицею embedding просто не існує.

# %%

def learned_position_encoding(length, table):
    """Повертає перші length рядків навченої позиційної таблиці."""

    # Поверніть копії рядків, щоб результат не змінював саму таблицю.
    ...


def test_learned_position_encoding():
    table = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
        [0.7, 0.8, 0.9],
    ]
    result = learned_position_encoding(2, table)
    assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    result[0][0] = 999
    assert table[0][0] == 0.1

    try:
        learned_position_encoding(4, table)
    except ValueError:
        pass
    else:
        raise AssertionError("length перевищує максимальну довжину таблиці")


if __name__ == "__main__":
    test_learned_position_encoding()
    print("✓ learned positional encoding")

# %% [markdown]
# ## 7. Навчувані Fourier features
#
# Синусоїдальне кодування використовує частоти, які наперед задані формулою.
# Можна зберегти ту саму ідею, але дозволити моделі **навчити частоти** разом
# з іншими параметрами:
#
# $$FF(pos) = [\sin(pos \cdot f_0), \cos(pos \cdot f_0), \ldots,
#               \sin(pos \cdot f_k), \cos(pos \cdot f_k)]$$
#
# Тут $f_0, \ldots, f_k$ — навчувані параметри. Позиційний вектор, як і раніше,
# просто додається до embedding токена. Сам механізм attention змінювати не
# потрібно.
#
# Спочатку передамо готові значення й дослідимо, як різні частоти змінюють
# кодування. Після цього навчимо їх у маленькому експерименті з PyTorch.

# %%

def fourier_position_encoding(length, frequencies):
    """Кодує позиції парами sin/cos із заданими навчуваними частотами."""

    # Для кожної позиції pos і кожної частоти f додайте спочатку sin(pos * f),
    # а потім cos(pos * f). Розмір результату: (length, 2 * len(frequencies)).
    ...


def test_fourier_position_encoding():
    from math import cos, isclose, sin

    frequencies = [1.0, 0.1]
    encoded = fourier_position_encoding(3, frequencies)

    assert len(encoded) == 3
    assert all(len(row) == 4 for row in encoded)
    assert encoded[0] == [0.0, 1.0, 0.0, 1.0]
    assert isclose(encoded[1][0], sin(1.0), rel_tol=1e-9)
    assert isclose(encoded[1][1], cos(1.0), rel_tol=1e-9)
    assert isclose(encoded[1][2], sin(0.1), rel_tol=1e-9)
    assert isclose(encoded[1][3], cos(0.1), rel_tol=1e-9)
    assert encoded[1] != encoded[2]

    assert fourier_position_encoding(2, []) == [[], []]

    try:
        fourier_position_encoding(-1, frequencies)
    except ValueError:
        pass
    else:
        raise AssertionError("length не може бути від'ємним")


if __name__ == "__main__":
    test_fourier_position_encoding()
    print("✓ Fourier positional encoding")

# Питання:
# - Що зміниться, якщо всі частоти будуть дуже малими?
# - Чому для кожної частоти використовуються і `sin`, і `cos`?
# - Які параметри цієї функції оновлював би gradient descent?
# - Чим цей підхід відрізняється від фіксованого синусоїдального кодування?

# %% [markdown]
# ## 8. Просте навчання позицій з PyTorch
#
# Досі ми лише обчислювали позиційні вектори. Тепер перевіримо, чи справді вони
# несуть корисну інформацію. Створимо навмисно просту задачу:
#
# - маємо 8 однакових токенів із нульовими embedding-векторами;
# - один спільний лінійний шар має визначити позицію кожного токена від 0 до 7;
# - порівняємо відсутність кодування, learned embedding та Fourier features.
#
# Без позиційного кодування всі вісім входів однакові. Одна й та сама функція
# не може дати для них вісім різних відповідей, тому найкраща accuracy — `1/8`.
# Позиційне кодування робить входи різними, і задача стає розв'язуваною.
#
# Це не тренування мовної моделі, а контрольований експеримент. Тут PyTorch
# зручний, бо автоматично обчислює градієнти та оновлює параметри.

# %%

def train_position_probe(encoding, length=8, d_model=8, steps=300):
    """Навчає простий класифікатор позиції та повертає його accuracy."""
    import torch

    if encoding not in {"none", "learned", "fourier"}:
        raise ValueError("encoding має бути none, learned або fourier")
    if d_model % 2 != 0:
        raise ValueError("d_model має бути парним")

    torch.manual_seed(0)
    positions = torch.arange(length)
    classifier = torch.nn.Linear(d_model, length)

    parameters = list(classifier.parameters())
    if encoding == "learned":
        position_encoder = torch.nn.Embedding(length, d_model)
        parameters += list(position_encoder.parameters())
    elif encoding == "fourier":
        # nn.Parameter повідомляє PyTorch, що ці частоти треба навчати.
        frequencies = torch.nn.Parameter(
            torch.randn(d_model // 2) * 0.2
        )
        parameters.append(frequencies)

    optimizer = torch.optim.Adam(parameters, lr=0.05)

    for _ in range(steps):
        if encoding == "none":
            inputs = torch.zeros(length, d_model)
        elif encoding == "learned":
            inputs = position_encoder(positions)
        else:
            angles = positions.float()[:, None] * frequencies[None, :]
            inputs = torch.stack(
                (torch.sin(angles), torch.cos(angles)), dim=-1
            ).flatten(start_dim=1)

        logits = classifier(inputs)
        loss = torch.nn.functional.cross_entropy(logits, positions)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        if encoding == "none":
            inputs = torch.zeros(length, d_model)
        elif encoding == "learned":
            inputs = position_encoder(positions)
        else:
            angles = positions.float()[:, None] * frequencies[None, :]
            inputs = torch.stack(
                (torch.sin(angles), torch.cos(angles)), dim=-1
            ).flatten(start_dim=1)
        predictions = classifier(inputs).argmax(dim=1)
        accuracy = (predictions == positions).float().mean()
    return accuracy.item()


def run_position_experiment():
    without_position = train_position_probe("none")
    learned = train_position_probe("learned")
    fourier = train_position_probe("fourier")

    print(f"Без позиційного кодування: {without_position:.1%}")
    print(f"Learned embeddings:       {learned:.1%}")
    print(f"Fourier features:         {fourier:.1%}")

    assert without_position <= 1 / 8
    assert learned > 0.95
    assert fourier > 0.95


if __name__ == "__main__":
    run_position_experiment()

# Питання:
# - Чому збільшення кількості кроків не допоможе варіанту `none`?
# - Які параметри навчаються у кожному з трьох експериментів?
# - Чому цей результат показує необхідність позиційної інформації, але ще не
#   доводить, який спосіб буде найкращим для мовної моделі?

# %% [markdown]
# ## 9. Порівняння підходів
#
# | Кодування | Навчені параметри | Позиції поза train | Компроміс |
# |---|---:|---|---|
# | синусоїдальне | 0 | можна обчислити | частоти задані вручну |
# | learned absolute | `max_length × d_model` | немає рядка | гнучке, але має фіксовану таблицю |
# | Fourier features | кілька частот | можна обчислити | компактне й адаптивне |
#
# Фінальні питання:
# - Чи змінить синусоїдальне кодування перестановка двох токенів? Де саме?
# - Чому learned-таблиця не може безпосередньо обробити позицію `max_length`?
# - Чому Fourier features можна обчислити для позиції, якої не було під час
#   тренування, навіть якщо самі частоти навчувані?
# - Чому позиційне кодування потрібне навіть тоді, коли токенізатор зберіг
#   правильний порядок токенів у списку?
# - Які два компроміси ми бачили: у виборі розміру токена та у виборі способу
#   кодування позиції?
