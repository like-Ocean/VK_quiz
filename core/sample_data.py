from models.question import AnswerType

SAMPLE_QUIZZES = [
    {
        "title": "Общие знания",
        "description": "Проверь свои знания в разных областях!",
        "category": "Общее",
        "time_per_question": 30,
        "questions": [
            {
                "text": "Сколько планет в Солнечной системе?",
                "order": 1,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("7", False), ("8", True), ("9", False), ("10", False)
                ]
            },
            {
                "text": "Какой самый большой океан на Земле?",
                "order": 2,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("Атлантический", False), ("Индийский", False),
                    ("Тихий", True), ("Северный Ледовитый", False)
                ]
            },
            {
                "text": "В каком году была основана компания Apple?",
                "order": 3,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("1972", False), ("1976", True), ("1980", False), ("1984", False)
                ]
            },
            {
                "text": "Какие из этих животных являются млекопитающими?",
                "order": 4,
                "points": 150,
                "answer_type": AnswerType.multiple,
                "options": [
                    ("Дельфин", True), ("Акула", False),
                    ("Летучая мышь", True), ("Крокодил", False)
                ]
            },
            {
                "text": "Кто написал роман «Война и мир»?",
                "order": 5,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("Достоевский", False), ("Чехов", False),
                    ("Толстой", True), ("Тургенев", False)
                ]
            },
        ]
    },
    {
        "title": "История мира",
        "description": "Тест на знание ключевых исторических событий.",
        "category": "История",
        "time_per_question": 25,
        "questions": [
            {
                "text": "В каком году началась Вторая мировая война?",
                "order": 1,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("1935", False), ("1937", False), ("1939", True), ("1941", False)
                ]
            },
            {
                "text": "Кто был первым президентом США?",
                "order": 2,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("Томас Джефферсон", False), ("Джордж Вашингтон", True),
                    ("Авраам Линкольн", False), ("Бенджамин Франклин", False)
                ]
            },
            {
                "text": "В каком году пала Берлинская стена?",
                "order": 3,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("1987", False), ("1989", True), ("1991", False), ("1993", False)
                ]
            },
            {
                "text": "Какая страна первой запустила человека в космос?",
                "order": 4,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("США", False), ("СССР", True), ("Германия", False), ("Китай", False)
                ]
            },
            {
                "text": "Кто из правителей построил Великую Китайскую стену?",
                "order": 5,
                "points": 150,
                "answer_type": AnswerType.single,
                "options": [
                    ("Конфуций", False), ("Чингисхан", False),
                    ("Цинь Шихуанди", True), ("Мао Цзэдун", False)
                ]
            },
        ]
    },
    {
        "title": "Мир технологий",
        "description": "Насколько хорошо ты разбираешься в IT и технологиях?",
        "category": "Технологии",
        "time_per_question": 20,
        "questions": [
            {
                "text": "Что означает аббревиатура HTTP?",
                "order": 1,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("HyperText Transfer Protocol", True),
                    ("High Tech Transfer Process", False),
                    ("HyperText Transmission Path", False),
                    ("Hybrid Transfer Technology Protocol", False)
                ]
            },
            {
                "text": "Какой язык программирования создал Гвидо ван Россум?",
                "order": 2,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("Java", False), ("Ruby", False), ("Python", True), ("Perl", False)
                ]
            },
            {
                "text": "Сколько бит в одном байте?",
                "order": 3,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("4", False), ("8", True), ("16", False), ("32", False)
                ]
            },
            {
                "text": "Какие из этих языков являются компилируемыми?",
                "order": 4,
                "points": 150,
                "answer_type": AnswerType.multiple,
                "options": [
                    ("C++", True), ("Python", False), ("Go", True), ("JavaScript", False)
                ]
            },
            {
                "text": "Кто основал компанию Tesla?",
                "order": 5,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("Только Илон Маск", False),
                    ("Мартин Эберхард и Марк Тарпеннинг", True),
                    ("Джефф Безос", False),
                    ("Стив Джобс", False)
                ]
            },
        ]
    },
    {
        "title": "Кино: классика и современность",
        "description": "Тест для настоящих киноманов.",
        "category": "Кино",
        "time_per_question": 30,
        "questions": [
            {
                "text": "Кто снял фильм «Начало» (Inception, 2010)?",
                "order": 1,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("Стивен Спилберг", False), ("Кристофер Нолан", True),
                    ("Джеймс Кэмерон", False), ("Ридли Скотт", False)
                ]
            },
            {
                "text": "Сколько «Оскаров» получил фильм «Титаник» (1997)?",
                "order": 2,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("9", False), ("11", True), ("7", False), ("14", False)
                ]
            },
            {
                "text": "Какой актёр сыграл Железного человека в киновселенной Marvel?",
                "order": 3,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("Крис Эванс", False), ("Крис Хемсворт", False),
                    ("Роберт Дауни мл.", True), ("Марк Руффало", False)
                ]
            },
            {
                "text": "В каком году вышел первый фильм «Звёздные войны»?",
                "order": 4,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("1975", False), ("1977", True), ("1980", False), ("1983", False)
                ]
            },
            {
                "text": "Какие фильмы сняты режиссёром Квентином Тарантино?",
                "order": 5,
                "points": 150,
                "answer_type": AnswerType.multiple,
                "options": [
                    ("Криминальное чтиво", True), ("Матрица", False),
                    ("Бесславные ублюдки", True), ("Бойцовский клуб", False)
                ]
            },
        ]
    },
    {
        "title": "Наука и природа",
        "description": "Проверь свои знания в биологии, химии и физике.",
        "category": "Наука",
        "time_per_question": 25,
        "questions": [
            {
                "text": "Какой элемент имеет химический символ Au?",
                "order": 1,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("Серебро", False), ("Алюминий", False),
                    ("Золото", True), ("Медь", False)
                ]
            },
            {
                "text": "Сколько хромосом в клетках человека?",
                "order": 2,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("23", False), ("44", False), ("46", True), ("48", False)
                ]
            },
            {
                "text": "Какова скорость света в вакууме (приблизительно)?",
                "order": 3,
                "points": 100,
                "answer_type": AnswerType.single,
                "options": [
                    ("150 000 км/с", False), ("300 000 км/с", True),
                    ("500 000 км/с", False), ("1 000 000 км/с", False)
                ]
            },
            {
                "text": "Какое животное имеет самое высокое кровяное давление?",
                "order": 4,
                "points": 150,
                "answer_type": AnswerType.single,
                "options": [
                    ("Слон", False), ("Жираф", True),
                    ("Синий кит", False), ("Лошадь", False)
                ]
            },
            {
                "text": "Какие из этих газов входят в состав воздуха?",
                "order": 5,
                "points": 150,
                "answer_type": AnswerType.multiple,
                "options": [
                    ("Азот", True), ("Водород", False),
                    ("Кислород", True), ("Хлор", False)
                ]
            },
        ]
    },
]