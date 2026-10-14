"""Построить отчёт из фактически полученных доказательств, без вымышленных ID."""
from __future__ import annotations

import json
from pathlib import Path


def table(rows: list[dict]) -> str:
    lines = ["| Файл | SHA-256 | Форма | Пропуски |", "|---|---|---|---|"]
    for row in rows:
        lines.append(f"| `{row['path']}` | `{row['sha256']}` | {row['rows']} × {row['column_count']} | {row['missing_values']} |")
    lines.append("")
    for row in rows:
        lines.append(f"Столбцы `{row['path']}`: " + ", ".join(f"`{column}`" for column in row["columns"]) + ".")
    return "\n\n".join(["\n".join(lines[:2 + len(rows)]), *lines[3 + len(rows):]])


def build_report(root: Path) -> None:
    dvc = json.loads((root / "evidence/dvc.json").read_text(encoding="utf-8"))
    clearml_path = root / "evidence/clearml.json"
    clearml = json.loads(clearml_path.read_text(encoding="utf-8")) if clearml_path.exists() else None
    complete = clearml is not None and len(clearml["versions"]) == 3
    lines = ["# Практическая работа №3. Версионирование данных с DVC и ClearML",
             "Автор: Gubeev. Дата локального выполнения: 14.10.2026.",
             "## Статус выполнения",
             "DVC выполнен и проверен. " + ("Три версии ClearML созданы, скачаны и проверены по ID." if complete else
             "ClearML пока не выполнен: учебный сервер и аккаунт не предоставлены, SDK не настроен. Скрипт подготовлен; Dataset IDs и наблюдения сервера не подменяются ожидаемыми результатами. Работа до завершения этой части не готова к полной сдаче."),
             "## Окружение и репозиторий",
             "| Компонент | Фактическая версия |\n|---|---|",
             *[f"| {name} | {value} |" for name, value in dvc["environment"].items()],
             "Прямые зависимости зафиксированы в `pyproject.toml`, транзитивные — в `poetry.lock`. Python ограничен веткой 3.12.",
             f"Локальный Git-репозиторий: [{root.name}]({root.as_posix()}). Основная ветка — `main`. Публичный URL пока отсутствует; после загрузки репозитория в Git-хостинг его следует добавить в этот раздел.",
             "## Подготовка и проверка таблиц",
             "`prepare_data.py` сортирует строки по всем исходным признакам и target (mergesort), сохраняет исходный порядок столбцов, UTF-8, LF, без индекса, `float_format=\"%.17g\"`. Новые признаки добавляются последними. Каждый режим перезаписывает только свой CSV, поэтому для состояния base используется пустая папка либо DVC checkout базовой версии.",
             "`check_data.py` проверяет точный состав выбранной версии, порядок столбцов, отсутствие индекса и пропусков, число строк, все исходные значения и target, порядок строк и формулы площадей. Для вещественных значений допускается ошибка 1e-12.",
             "Проверки генератора и валидатора: " + "; ".join(dvc["checks"]) + ".",
             "## Версии DVC",
             "| Состояние | Git commit | Tag/ветка при создании | DVC directory MD5 | SHA-256 data.dvc |\n|---|---|---|---|---|"]
    for state, row in dvc["versions"].items():
        lines.append(f"| {state} | `{row['commit']}` | `{row['ref']}` | `{row['directory_md5']}` | `{row['metadata_sha256']}` |")
    for state, row in dvc["versions"].items():
        lines.extend([f"### {state}", table(row["tables"])])
    lines.extend(["### Ветвление, слияние и remote",
                  "`feature/wine` и `feature/iris-features` созданы от общей базы main. Первая добавляет Wine и сохраняет SHA-256 Iris; вторая изменяет Iris и не содержит Wine. Переключение обратно в main проверено после `dvc checkout`: Wine исчез, хэш Iris совпал с data-v1.",
                  "В `.gitattributes` сохранено `*.dvc merge=dvc`. В локальной конфигурации Git настроен `dvc git-hook merge-driver --ancestor %O --our %A --their %B`; новый clone должен настроить этот driver самостоятельно для будущих слияний.",
                  dvc["merge_observation"],
                  f"Родители merge-коммита: `{dvc['merge_parents']}`. История обеих ветвей сохранена. main получила проверенный merge через fast-forward. Маркеры конфликта в data.dvc отсутствуют.",
                  f"Remote `storage`: `{dvc['remote']}`. Это соседняя директория вне репозитория. Безопасная конфигурация сохранена в `.dvc/config`. Все версии отправлены через dvc push; повторный push --all-commits не обнаружил недостающих объектов.",
                  "CSV не входят ни в один Git-коммит; cache и локальные настройки игнорируются. Файлы cache вручную не изменялись.",
                  "### Восстановление из чистого clone",
                  f"Создан новый clone `{dvc['clone']}`. До dvc pull: data отсутствовала, локальный cache отсутствовал. Cache исходного репозитория не копировался и не использовался как shared cache.",
                  "После dvc pull SHA-256, формы и столбцы совпали с итоговым состоянием. Дополнительно data-v1 восстановлен из remote в том же clone, затем итоговая main получена снова. Это проверяет доступность базовой и итоговой версий независимо от старого cache.",
                  f"Итоговый `dvc status --json`: `{json.dumps(dvc['status'])}`. `git status --short`: пустой после сохранения отчёта.",
                  table(dvc["clone_tables"]),
                  "Локальный remote доступен только на этом компьютере. Для восстановления на другом компьютере нужно перенести remote отдельно или заменить его общим сетевым/S3-хранилищем; загрузка только Git-репозитория не передаёт CSV.",
                  "## ClearML Dataset"])
    if complete:
        lines.extend([f"Project: `{clearml['project']}`. Dataset name: `{clearml['name']}`.",
                      *[f"- `{key}`: `{value}`" for key, value in clearml["ids"].items()],
                      "Все три версии финализированы и получены строго по ID; скачаны в разные пустые директории. get_mutable_local_copy может использовать SDK cache; скачивание на второй физической машине отдельно не проверялось."])
        for version in clearml["versions"]:
            lines.extend([f"### Version {version['version']}",
                          f"ID: `{version['id']}`. Parents: `{version['parents']}`. Полный список: `{version['files']}`.",
                          f"Added: `{version['changes']['added']}`; modified: `{version['changes']['modified']}`; removed: `{version['changes']['removed']}`.",
                          "Dependency graph:\n```json\n" + json.dumps(version["graph"], indent=2) + "\n```",
                          table(version["tables"])])
        lines.append("База после создания обеих дочерних версий по-прежнему содержит только iris.csv. WINE_ID отсутствует среди предков IRIS_FEATURES_ID. Хэши скачанных файлов совпадают с независимой локальной генерацией.")
    else:
        lines.extend(["`BASE_ID`, `WINE_ID`, `IRIS_FEATURES_ID`: **ещё не получены**. Реальные dependency graph, статус Completed, состав и SHA-256 скачанных версий будут автоматически добавлены после успешного запуска `clearml_versions.py`.",
                      "Подготовленная схема (ожидаемая, не измеренный граф сервера):\n```text\n1.0.0 (BASE_ID): iris.csv\n├── 1.1.0 (WINE_ID): исходный iris.csv + wine.csv\n└── 2.0.0 (IRIS_FEATURES_ID): iris.csv с двумя площадями, без wine.csv\n```",
                      "Скрипт создаёт обе дочерние версии с единственным parent BASE_ID, добавляет в 1.1.0 только wine.csv, в 2.0.0 только изменённый iris.csv; вызывает upload до finalize. Затем получает каждую версию по ID, проверяет parents, added/modified/removed, полный состав и локальные хэши. ID сохраняются сразу после создания, поэтому повторный запуск продолжает работу с теми же объектами.",
                      "Инструкция настройки и запуска находится в README.md. Credentials не записаны в код, Git или отчёт."])
    cm_note = "Наблюдения подтверждены evidence/clearml.json" if complete else "ClearML ниже описан по подготовленному коду и SDK; наблюдения сервера пока отсутствуют"
    lines.extend(["## Сравнение", cm_note + ".",
                  "| Свойство | DVC: наблюдение в работе | ClearML Dataset |\n|---|---|---|",
                  "| Идентификатор версии | В таблице записаны Git commit + directory MD5 и SHA-256 метафайла | Точные BASE_ID/WINE_ID/IRIS_FEATURES_ID; номер версии задаётся отдельно |",
                  "| Метаданные | data.dvc и .dvc/config находятся в Git | Dataset на сервере, SDK получает его по ID |",
                  "| Файлы | CSV в workspace, cache и соседнем remote; Git их не содержит | upload отправляет новые/изменённые файлы в configured storage; дочерняя версия наследует Iris |",
                  "| Дочерняя версия | От базы созданы два Git-коммита в двух ветках | Dataset.create с явным parent_datasets=[BASE_ID] |",
                  "| Переключение | После switch main и checkout Wine исчез, Iris восстановился | Dataset.get(dataset_id=...) и отдельная локальная копия каждой версии |",
                  "| Чистая машина | Clone без data/cache восстановлен через dvc pull из remote | Нужны SDK, credentials, доступ к server/storage; get по ID и download |",
                  "| Ветвление | feature/wine и feature/iris-features имеют общую базу | 1.1.0 и 2.0.0 явно наследуют одну базу |",
                  "| Слияние | Merge driver объединил изменение Iris и добавление Wine; проверены оба SHA-256 | Слияние в этой части задания не выполняется; SDK допускает несколько parents |",
                  "| Связь с Git | Версии data.dvc зафиксированы отдельными коммитами и data-v1 | Git хранит код и ID в отчёте; Dataset ID существует независимо от Git |",
                  "| UI | В работе использованы CLI, git log и data.dvc | Проверка Web UI пока не выполнена; SDK проверяет финализацию и lineage |" if not complete else
                  "| UI | В работе использованы CLI, git log и data.dvc | Метаданные доступны серверу; SDK проверил финализацию, Web UI отдельно не проверялся |",
                  "## Ответы на вопросы",
                  "1. **Что определяет версию DVC?** Содержимое отслеживаемой директории задаётся content hash `.dir` в data.dvc, который ссылается на манифест с хэшами файлов. Git commit фиксирует конкретную редакцию этого метафайла и кода. SHA-256 метафайла полезен для проверки байтов; сам по себе он не является хэшем содержимого всех CSV. Разные коммиты могут ссылаться на одни данные.",
                  "2. **Почему коммита мало?** Git содержит указатель на объекты, но не CSV. Если cache утрачен и remote отсутствует, указанные объекты скачать неоткуда. В работе clone получил файлы именно из отдельного remote.",
                  "3. **Version и ID ClearML.** Version — задаваемый человеком семантический номер (1.0.0 и т.д.), ID — уникальная идентичность конкретного Dataset. Для восстановления скрипт использует ID; одинаковые подписи версии не заменяют идентификатор.",
                  "4. **Почему finalize не создаёт следующую версию?** finalize закрывает текущий Dataset для изменения. Следующая версия создаётся отдельным Dataset.create с новым ID и явными родителями.",
                  "5. **Как доказать происхождение 2.0.0?** В измеренном get_dependency_graph проверяют graph[IRIS_FEATURES_ID] == [BASE_ID], а WINE_ID отсутствует среди предков. Дополнительно состав 2.0.0 не содержит Wine. Один только состав файлов не доказывает lineage. Сейчас эта проверка реализована в скрипте" + (" и выполнена." if complete else ", но до подключения к серверу не выполнена."),
                  "6. **Switch без DVC checkout.** Git изменит data.dvc, но CSV могут остаться от прежней ветки. Код будет читать состояние, не соответствующее Git; dvc status покажет расхождение. В работе workspace приводился к версии main явно через checkout.",
                  "7. **Где удобнее каждый инструмент?** DVC удобен для двух Git-веток и слияния независимых изменений Iris/Wine: история данных идёт вместе с кодом. ClearML Dataset удобен для выдачи финализированных версий по ID и просмотра родительского графа в общем сервере, без переключения Git. Сравнение удобства ClearML пока основано на подготовленном сценарии" + (" и проверке SDK." if complete else ", а не на выполненной серверной части."),
                  "## Источники",
                  "- [DVC merge driver](https://dvc.org/doc/user-guide/how-to/resolve-merge-conflicts)",
                  "- [ClearML Dataset SDK](https://clear.ml/docs/latest/docs/references/sdk/dataset/)",
                  "Исходное задание: data_versioning_practice.md; справочник: explained.md. Демонстрационный notebook выполнялся отдельно и не использован вместо самостоятельного решения."])
    (root / "REPORT.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build_report(Path(__file__).resolve().parent)
