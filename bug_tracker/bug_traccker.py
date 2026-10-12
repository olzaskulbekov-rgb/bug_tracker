# bug_tracker.py
# Мини-трекер ошибок EKEB / Т118


def find_bug(bugs, bug_id):
    """
    Возвращает словарь с указанным ID, либо None, если записи нет.
    Ищем по полю "id", а не по индексу списка, потому что порядок
    записей в списке может не совпадать с их ID (например, после
    удаления, перестановки или если ID начинаются не с 1).
    bugs[bug_id - 1] ненадёжен: если записи переставить местами
    или ID окажутся не по порядку, он вернёт не ту запись либо
    вызовет ошибку выхода за границы списка.
    """
    for bug in bugs:
        if bug["id"] == bug_id:
            return bug
    return None


def filter_bugs(bugs, status, severity):
    """
    Возвращает новый список записей, у которых status И severity
    одновременно совпадают с переданными параметрами (здесь нужен
    именно and: and требует выполнения обоих условий сразу, тогда
    как or вернул бы записи, подходящие хотя бы по одному критерию,
    то есть результат оказался бы шире, чем "отбор по двум условиям").
    Параметры очищаются от пробелов по краям и приводятся к нижнему
    регистру, чтобы "OPEN" и " open " считались одинаковыми.
    Исходные словари не изменяются - в результат попадают те же
    объекты, без копирования.
    """
    status = status.strip().lower()
    severity = severity.strip().lower()

    result = []
    for bug in bugs:
        if bug["status"] == status and bug["severity"] == severity:
            result.append(bug)
    return result


def add_bug(bugs, title, severity):
    """
    Добавляет новую запись со статусом "open" и возвращает её ID.
    Если данные некорректны, возвращает None и список не меняет.

    Новый ID = (максимальный существующий ID) + 1, а не len(bugs) + 1.
    len(bugs) + 1 ненадёжен: если из списка удалить запись, его длина
    уменьшится, и новый ID может случайно совпасть с уже существующим
    (например, были ID 1-4, удалили запись с ID 2 - длина стала 3,
    len(bugs)+1 даст 4, хотя ID 4 уже занят).
    """
    title = title.strip()
    severity = severity.strip().lower()

    if len(title) < 5:
        return None
    if severity not in ("low", "medium", "high"):
        return None

    if len(bugs) == 0:
        new_id = 1
    else:
        new_id = max(bug["id"] for bug in bugs) + 1

    bugs.append({
        "id": new_id,
        "title": title,
        "severity": severity,
        "status": "open"
    })
    return new_id


def change_status(bugs, bug_id, new_status):
    """
    Меняет статус записи с проверкой разрешённых переходов:
    open -> in_progress
    in_progress -> open или closed
    closed -> open
    Переход в тот же статус запрещён.

    Порядок действий: сначала проверяем new_status, затем ищем запись,
    затем проверяем сам переход, и только после этого меняем статус -
    так при любом отказе исходные данные гарантированно не меняются.

    Возврат:
    "updated"         - статус изменён
    "invalid_status"  - new_status не входит в допустимые значения
    "not_found"       - запись с таким ID не найдена
    "forbidden"       - переход запрещён правилами (в т.ч. переход в тот же статус)
    """
    new_status = new_status.strip().lower()
    if new_status not in ("open", "in_progress", "closed"):
        return "invalid_status"

    bug = find_bug(bugs, bug_id)
    if bug is None:
        return "not_found"

    allowed_transitions = {
        "open": ["in_progress"],
        "in_progress": ["open", "closed"],
        "closed": ["open"]
    }

    if new_status in allowed_transitions[bug["status"]]:
        bug["status"] = new_status
        return "updated"
    else:
        return "forbidden"


def build_report(bugs):
    """
    Собирает статистику по текущему списку ошибок:
    total           - общее число записей
    by_status       - количество записей по каждому статусу
    by_severity     - количество записей по каждой серьёзности
    unresolved_high - число записей с severity "high", чей статус
                       не равен "closed" (то есть ещё не решённые)

    Счётчики by_status и by_severity сразу создаются со всеми
    возможными ключами и нулями, поэтому для пустого списка
    структура результата сохраняется, просто все значения - 0.
    Исходные записи не изменяются.
    """
    report = {
        "total": 0,
        "by_status": {"open": 0, "in_progress": 0, "closed": 0},
        "by_severity": {"low": 0, "medium": 0, "high": 0},
        "unresolved_high": 0
    }

    for bug in bugs:
        report["total"] += 1
        report["by_status"][bug["status"]] += 1
        report["by_severity"][bug["severity"]] += 1
        if bug["severity"] == "high" and bug["status"] != "closed":
            report["unresolved_high"] += 1

    return report


def start_selected(bugs, ids):
    """
    Переводит выбранные по ID записи из "open" в "in_progress".
    Действует по принципу "всё или ничего": сначала полностью
    проверяется весь набор ID, и только если он целиком корректен,
    происходят изменения. Так исключается ситуация, когда часть
    записей уже изменена, а на середине списка операция прервалась.

    Возвращает False без каких-либо изменений данных, если:
    - ids пуст,
    - в ids есть повторяющийся ID,
    - хотя бы один ID отсутствует в bugs,
    - хотя бы одна из выбранных записей не в статусе "open".

    Возвращает True и меняет статусы, если весь набор корректен.
    """
    if len(ids) == 0:
        return False

    if len(ids) != len(set(ids)):
        return False

    for bug_id in ids:
        bug = find_bug(bugs, bug_id)
        if bug is None:
            return False
        if bug["status"] != "open":
            return False

    for bug_id in ids:
        bug = find_bug(bugs, bug_id)
        bug["status"] = "in_progress"

    return True


# ---------- Вспомогательные функции для меню ----------

def parse_positive_int(text):
    """
    Пытается превратить введённый текст в положительное целое число.
    Возвращает число либо None, если ввод некорректен (буквы, дроби,
    отрицательные числа, ноль, пустая строка). Используется в меню,
    чтобы некорректный ввод не останавливал программу и не доходил
    до функций обработки данных.
    """
    text = text.strip()
    if not text.isdigit():
        return None
    value = int(text)
    if value <= 0:
        return None
    return value


def print_bug(bug):
    print(f"ID {bug['id']} | {bug['title']} | "
          f"серьёзность: {bug['severity']} | статус: {bug['status']}")


# ---------- Меню ----------

def main():
    bugs = [
        {"id": 1, "title": "Не работает вход", "severity": "high", "status": "open"},
        {"id": 2, "title": "Опечатка на главной странице", "severity": "low", "status": "closed"},
        {"id": 3, "title": "Не сохраняется расписание", "severity": "high", "status": "open"},
        {"id": 4, "title": "Неверный цвет кнопки", "severity": "medium", "status": "open"}
    ]

    while True:
        print("\n1. Показать все ошибки")
        print("2. Найти по ID")
        print("3. Отфильтровать")
        print("4. Добавить")
        print("5. Изменить статус")
        print("6. Показать отчёт")
        print("7. Назначить несколько ошибок в работу")
        print("0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "1":
            if len(bugs) == 0:
                print("Список ошибок пуст.")
            for bug in bugs:
                print_bug(bug)

        elif choice == "2":
            bug_id = parse_positive_int(input("Введите ID: "))
            if bug_id is None:
                print("Некорректный ID.")
                continue
            result = find_bug(bugs, bug_id)
            if result is None:
                print("Запись с таким ID не найдена.")
            else:
                print_bug(result)

        elif choice == "3":
            status = input("Статус (open/in_progress/closed): ")
            severity = input("Серьёзность (low/medium/high): ")
            result = filter_bugs(bugs, status, severity)
            if len(result) == 0:
                print("Совпадений не найдено.")
            for bug in result:
                print_bug(bug)

        elif choice == "4":
            title = input("Название (минимум 5 символов): ")
            severity = input("Серьёзность (low/medium/high): ")
            new_id = add_bug(bugs, title, severity)
            if new_id is None:
                print("Не удалось добавить запись: проверьте название и серьёзность.")
            else:
                print(f"Добавлено. Новый ID: {new_id}")

        elif choice == "5":
            bug_id = parse_positive_int(input("ID: "))
            if bug_id is None:
                print("Некорректный ID.")
                continue
            new_status = input("Новый статус (open/in_progress/closed): ")
            result = change_status(bugs, bug_id, new_status)
            messages = {
                "updated": "Статус обновлён.",
                "invalid_status": "Неизвестный статус.",
                "not_found": "Запись с таким ID не найдена.",
                "forbidden": "Такой переход статуса запрещён."
            }
            print(messages[result])

        elif choice == "6":
            report = build_report(bugs)
            print(f"Всего записей: {report['total']}")
            print(f"По статусу: {report['by_status']}")
            print(f"По серьёзности: {report['by_severity']}")
            print(f"Нерешённых high: {report['unresolved_high']}")

        elif choice == "7":
            raw = input("ID через пробел: ").strip()
            if raw == "":
                ids = []
            else:
                parts = raw.split()
                ids = []
                invalid_found = False
                for part in parts:
                    value = parse_positive_int(part)
                    if value is None:
                        invalid_found = True
                        break
                    ids.append(value)
                if invalid_found:
                    print("Среди введённых значений есть некорректный ID.")
                    continue

            result = start_selected(bugs, ids)
            if result:
                print("Выбранные записи переведены в работу.")
            else:
                print("Отказ: изменений не внесено.")

        elif choice == "0":
            print("Выход.")
            break

        else:
            print("Неизвестная команда.")


if __name__ == "__main__":
    main()
