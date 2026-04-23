#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных с демо-данными.
Запуск: python init_db.py
"""
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base, Lesson, Exercise
from config import DATABASE_URL

async def init_database():
    """Инициализация базы данных с демо-данными"""
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем сессию
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Создаем демо-уроки
        lessons_data = [
            {
                "title": "Введение в JavaScript",
                "description": "Основы языка JavaScript: синтаксис, переменные, типы данных",
                "content": """
# Введение в JavaScript

JavaScript — это язык программирования, который позволяет создавать интерактивные веб-страницы.

## Что такое JavaScript?
- JavaScript является языком сценариев
- Выполняется в браузере пользователя
- Поддерживает объектно-ориентированное программирование
- Не требует компиляции

## Переменные
В JavaScript есть три способа объявления переменных:
1. `var` — устаревший способ, имеет функциональную область видимости
2. `let` — современный способ, имеет блочную область видимости
3. `const` — для констант, значение нельзя изменить

Пример:
\`\`\`javascript
let name = "Иван";
const age = 25;
var city = "Москва"; // не рекомендуется
\`\`\`

## Типы данных
JavaScript имеет динамическую типизацию. Основные типы:
- Числа: `42`, `3.14`
- Строки: `"Привет"`
- Булевы значения: `true`, `false`
- `null` и `undefined`
- Объекты и массивы

## Консоль разработчика
Для отладки используйте `console.log()`:
\`\`\`javascript
console.log("Привет, мир!");
console.log(2 + 2);
\`\`\`
                """,
                "order": 1,
                "difficulty": "beginner",
                "estimated_time": 15
            },
            {
                "title": "Условные операторы и циклы",
                "description": "Изучаем if/else, switch, for, while для управления потоком выполнения",
                "content": """
# Условные операторы и циклы

## Условные операторы
### if/else
\`\`\`javascript
let temperature = 25;

if (temperature > 30) {
    console.log("Жарко");
} else if (temperature > 20) {
    console.log("Тепло");
} else {
    console.log("Прохладно");
}
\`\`\`

### Тернарный оператор
\`\`\`javascript
let age = 18;
let canVote = age >= 18 ? "Можно" : "Нельзя";
console.log(canVote); // "Можно"
\`\`\`

### switch
\`\`\`javascript
let day = "понедельник";

switch(day) {
    case "понедельник":
        console.log("Начало недели");
        break;
    case "пятница":
        console.log("Конец недели");
        break;
    default:
        console.log("Обычный день");
}
\`\`\`

## Циклы
### for
\`\`\`javascript
for (let i = 0; i < 5; i++) {
    console.log(i); // 0, 1, 2, 3, 4
}
\`\`\`

### while
\`\`\`javascript
let count = 0;
while (count < 3) {
    console.log(count);
    count++;
}
\`\`\`

### do...while
\`\`\`javascript
let x = 0;
do {
    console.log(x);
    x++;
} while (x < 3);
\`\`\`

## Управление циклами
- `break` — прерывает выполнение цикла
- `continue` — пропускает текущую итерацию

\`\`\`javascript
for (let i = 0; i < 10; i++) {
    if (i === 5) break; // цикл прервется при i = 5
    if (i % 2 === 0) continue; // пропустит четные числа
    console.log(i); // выведет только нечетные числа меньше 5
}
\`\`\`
                """,
                "order": 2,
                "difficulty": "beginner",
                "estimated_time": 20
            },
            {
                "title": "Функции в JavaScript",
                "description": "Создание и использование функций, параметры, возвращаемые значения",
                "content": """
# Функции в JavaScript

Функции — это основные строительные блоки программы в JavaScript.

## Объявление функций
### Function Declaration
\`\`\`javascript
function greet(name) {
    return "Привет, " + name + "!";
}

console.log(greet("Анна")); // "Привет, Анна!"
\`\`\`

### Function Expression
\`\`\`javascript
const multiply = function(a, b) {
    return a * b;
};

console.log(multiply(3, 4)); // 12
\`\`\`

### Стрелочные функции (ES6+)
\`\`\`javascript
const square = (x) => x * x;
console.log(square(5)); // 25

const add = (a, b) => {
    const sum = a + b;
    return sum;
};
console.log(add(2, 3)); // 5
\`\`\`

## Параметры и аргументы
### Параметры по умолчанию
\`\`\`javascript
function greet(name = "Гость") {
    return "Привет, " + name;
}

console.log(greet()); // "Привет, Гость"
console.log(greet("Петр")); // "Привет, Петр"
\`\`\`

### Rest параметры
\`\`\`javascript
function sum(...numbers) {
    let total = 0;
    for (let num of numbers) {
        total += num;
    }
    return total;
}

console.log(sum(1, 2, 3)); // 6
console.log(sum(1, 2, 3, 4, 5)); // 15
\`\`\`

## Возвращаемые значения
Функция всегда возвращает значение. Если нет `return`, возвращается `undefined`.

\`\`\`javascript
function noReturn() {
    // нет return
}

console.log(noReturn()); // undefined
\`\`\`

## Замыкания
Функция имеет доступ к переменным из внешней области видимости.

\`\`\`javascript
function createCounter() {
    let count = 0;
    
    return function() {
        count++;
        return count;
    };
}

const counter = createCounter();
console.log(counter()); // 1
console.log(counter()); // 2
console.log(counter()); // 3
\`\`\`

## Рекурсия
Функция может вызывать саму себя.

\`\`\`javascript
function factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

console.log(factorial(5)); // 120
\`\`\`
                """,
                "order": 3,
                "difficulty": "beginner",
                "estimated_time": 25
            }
        ]
        
        # Добавляем уроки в базу
        lessons = []
        for lesson_data in lessons_data:
            lesson = Lesson(
                title=lesson_data["title"],
                description=lesson_data["description"],
                content=lesson_data["content"],
                order=lesson_data["order"],
                difficulty=lesson_data["difficulty"],
                estimated_time=lesson_data["estimated_time"]
            )
            session.add(lesson)
            lessons.append(lesson)
        
        await session.flush()  # Получаем ID уроков
        
        # Создаем упражнения для каждого урока
        exercises_data = [
            # Упражнения для урока 1
            {
                "lesson_id": lessons[0].id,
                "question": "Какой оператор используется для объявления переменной с блочной областью видимости в современном JavaScript?",
                "code_template": "",
                "correct_answer": "let",
                "answer_type": "text",
                "options": None,
                "explanation": "Ключевое слово `let` используется для объявления переменных с блочной областью видимости. `var` имеет функциональную область видимости, а `const` используется для констант.",
                "points": 10
            },
            {
                "lesson_id": lessons[0].id,
                "question": "Что выведет этот код?\n```javascript\nconsole.log(typeof 42);\n```",
                "code_template": "",
                "correct_answer": "number",
                "answer_type": "text",
                "options": None,
                "explanation": "Оператор `typeof` возвращает строку, указывающую тип операнда. Для числа 42 он вернет 'number'.",
                "points": 10
            },
            {
                "lesson_id": lessons[0].id,
                "question": "Выберите правильный способ объявления константы:",
                "code_template": "",
                "correct_answer": "3",
                "answer_type": "multiple_choice",
                "options": json.dumps([
                    "var PI = 3.14;",
                    "let PI = 3.14;",
                    "const PI = 3.14;",
                    "PI = 3.14;"
                ]),
                "explanation": "Ключевое слово `const` используется для объявления констант, значение которых нельзя изменить после инициализации.",
                "points": 15
            },
            
            # Упражнения для урока 2
            {
                "lesson_id": lessons[1].id,
                "question": "Напишите цикл for, который выводит числа от 1 до 5 включительно.",
                "code_template": "for (let i = 1; i <= 5; i++) {\n    console.log(i);\n}",
                "correct_answer": "for (let i = 1; i <= 5; i++) {\n    console.log(i);\n}",
                "answer_type": "code",
                "options": None,
                "explanation": "Цикл for состоит из трех частей: инициализации (let i = 1), условия (i <= 5) и инкремента (i++).",
                "points": 20
            },
            {
                "lesson_id": lessons[1].id,
                "question": "Что выведет этот код?\n```javascript\nlet x = 10;\nif (x > 5) {\n    console.log('Больше');\n} else {\n    console.log('Меньше или равно');\n}\n```",
                "code_template": "",
                "correct_answer": "Больше",
                "answer_type": "text",
                "options": None,
                "explanation": "Поскольку x = 10, условие x > 5 истинно, поэтому выполнится первая ветка if.",
                "points": 10
            },
            
            # Упражнения для урока 3
            {
                "lesson_id": lessons[2].id,
                "question": "Напишите стрелочную функцию, которая принимает два числа и возвращает их сумму.",
                "code_template": "const sum = (a, b) => a + b;",
                "correct_answer": "const sum = (a, b) => a + b;",
                "answer_type": "code",
                "options": None,
                "explanation": "Стрелочные функции позволяют писать более короткий синтаксис. Если тело функции состоит из одного выражения, можно опустить фигурные скобки и return.",
                "points": 20
            },
            {
                "lesson_id": lessons[2].id,
                "question": "Что такое замыкание (closure) в JavaScript?",
                "code_template": "",
                "correct_answer": "2",
                "answer_type": "multiple_choice",
                "options": json.dumps([
                    "Способ объявления переменных",
                    "Функция, которая запоминает свое лексическое окружение",
                    "Метод оптимизации кода",
                    "Тип данных в JavaScript"
                ]),
                "explanation": "Замыкание — это функция, которая запоминает переменные из своей внешней области видимости даже после того, как внешняя функция завершила выполнение.",
                "points": 15
            }
        ]
        
        # Добавляем упражнения в базу
        for exercise_data in exercises_data:
            exercise = Exercise(
                lesson_id=exercise_data["lesson_id"],
                question=exercise_data["question"],
                code_template=exercise_data["code_template"],
                correct_answer=exercise_data["correct_answer"],
                answer_type=exercise_data["answer_type"],
                options=exercise_data["options"],
                explanation=exercise_data["explanation"],
                points=exercise_data["points"]
            )
            session.add(exercise)
        
        await session.commit()
        print(f"✅ Добавлено {len(lessons)} уроков и {len(exercises_data)} упражнений")
    
    await engine.dispose()

if __name__ == "__main__":
    print("🚀 Инициализация базы данных с демо-данными...")
    asyncio.run(init_database())
    print("✅ База данных успешно инициализирована!")