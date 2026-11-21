# Практические работы №3–4. Версии данных и эксперименты

Автор: Gubeev. Локальная часть DVC выполнена 14.10.2026.

В работе подготовлены версии Iris и Wine, проверены ветвление, слияние и восстановление данных через DVC. В ClearML Dataset созданы три версии с проверкой состава, хэшей и связей между версиями.

## Версии данных

- `BASE_ID`: `77ab3b41f30a48a7b4da01a60e705aba`.
- `WINE_ID`: `fd4384d1b03242269ec15a584a543499`.
- `IRIS_FEATURES_ID`: `23306db43cc441fd8eb27f66502bf1a1`.
- `WINE_SHA256`: `b72adfd45219c12d4af882f76b4c67df0a44922d0bac0f2fd30e4b8d0c97a301`.

Хэш Wine из ClearML совпадает с итоговой версией DVC. Подробные результаты подготовки, восстановления и проверки приведены ниже.

## Файлы и запуск

| Скрипт | Назначение |
|---|---|
| `prepare_data.py` | Режимы base, wine и iris_features; изменяет только нужный CSV |
| `check_data.py` | Проверка состава, значений, столбцов и SHA-256 |
| `clearml_versions.py` | Базовая версия 1.0.0 и общие настройки ClearML |
| `clearml_wine.py` | Дочерняя версия 1.1.0 с Wine |
| `clearml_iris_features.py` | Независимая дочерняя версия 2.0.0 с признаками Iris |
| `download_clearml_versions.py` | Скачивание трёх версий строго по ID |
| `verify_clearml.py` | Проверка локальных файлов и серверных parents, статусов и изменений |

Проверка данных в подготовленном локальном окружении:

```powershell
..\.venv\Scripts\Activate.ps1
python check_data.py --version merged
python verify_clearml.py --fresh-cache --update-report
```

Скрипты `clearml_versions.py`, `clearml_wine.py` и `clearml_iris_features.py` без аргументов выводят сведения о версиях. Флаг `--execute` запускает получение и проверку существующих Dataset. Для создания версии в `create_version` предусмотрены добавление изменённого файла, загрузка и финализация. Идентификаторы существующих версий сохранены в коде и этом отчёте; повторная проверка не создаёт дубликаты.

Для отдельного скачивания используется `python download_clearml_versions.py`, для проверки — `python verify_clearml.py --update-report`. Копии данных и кэш SDK размещаются в игнорируемой директории `.dvc/tmp/clearml/`.

Для запуска на другом компьютере нужны `poetry install`, настройка ClearML командой `clearml-init` и доступ к DVC remote. Команда `poetry run dvc pull` восстанавливает итоговые CSV. В локальной конфигурации remote расположен в соседней папке `../dvc_remote_Gubeev`, окружение — в `../.venv`. Данные хранилища, окружение и конфигурация доступа не включены в Git.

## Окружение и репозиторий

| Компонент | Фактическая версия |
|---|---|
| Python | 3.12.10 |
| dvc | 3.59.2 |
| clearml | 1.18.0 |
| scikit-learn | 1.6.1 |
| pandas | 2.2.3 |
| poetry | 2.1.1 |

Прямые зависимости зафиксированы в `pyproject.toml`, транзитивные — в `poetry.lock`. Python ограничен веткой 3.12.

GitHub-репозиторий: [practice_3_mlops_Gubeev](https://github.com/Ilush1k/practice_3_mlops_Gubeev). Основная ветка — `main`. Локальная папка проекта — `mlops-data-Gubeev`.

## Подготовка и проверка таблиц

`prepare_data.py` сортирует строки по всем исходным признакам и target (mergesort), сохраняет исходный порядок столбцов, UTF-8, LF, без индекса, `float_format="%.17g"`. Новые признаки добавляются последними. Каждый режим перезаписывает только свой CSV, поэтому для состояния base используется пустая папка либо DVC checkout базовой версии.

`check_data.py` проверяет точный состав выбранной версии, порядок столбцов, отсутствие индекса и пропусков, число строк, все исходные значения и target, порядок строк и формулы площадей. Для вещественных значений допускается ошибка 1e-12.

Для всех трёх режимов проверены повторяемость байтов CSV и сохранность соседнего файла. Валидатор обнаруживает неверную площадь, изменённый target, потерянную строку, неверный порядок столбцов, индекс pandas, пропуски и отсутствие файла. При переключении Git-ветки без `dvc checkout` в рабочей директории оставался Wine из предыдущей версии.

## Версии DVC

| Состояние | Git commit | Tag/ветка при создании | DVC directory MD5 | SHA-256 data.dvc |
|---|---|---|---|---|
| base | `0e9ffa0705a1b5a6740d912a86c2519d08b594be` | `data-v1` | `68694d6e2fc4bf7a7da11d2b0d489e1e.dir` | `3aa2128aa15e4da33d4f63faa9c38edb24d1b02d1cab7cb8eb3d1c5d10bc596b` |
| wine | `d584f8acf48d56ef9845fffad13147e9df6aa8e8` | `feature/wine` | `cd692bf1d9bad578ff6e9bdaf5fff033.dir` | `1363389a0a3865e646f3d2b8cb1e71bd518af1f5fa21971272b77365e25e57df` |
| iris_features | `f57a83d753ab5ff8b28ab5153ca55de5ae49411c` | `feature/iris-features before merge (data-merged^1)` | `84fad98472f78577bceb6d442c1f794d.dir` | `c2574a6022983aaaeedd6a3722cfd498fb901e2434a1af930b258f883c266697` |
| merged | `0cb89b326214bebf41ba547d8e8c9b5c2ca1a9a1` | `main; data-merged` | `d23e2a33f1aa86af524072021da153ed.dir` | `53ae84294d6d0310b6dedf66e175c94afae61db8a05f6e7b226f0d591a289cb8` |

### base

| Файл | SHA-256 | Форма | Пропуски |
|---|---|---|---|
| `data/iris.csv` | `acb1d0e09be856a27d25798722572591b3ec55df2382354c5f83919f4b61e96b` | 150 × 5 | 0 |

Столбцы `data/iris.csv`: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`.

### wine

| Файл | SHA-256 | Форма | Пропуски |
|---|---|---|---|
| `data/iris.csv` | `acb1d0e09be856a27d25798722572591b3ec55df2382354c5f83919f4b61e96b` | 150 × 5 | 0 |
| `data/wine.csv` | `b72adfd45219c12d4af882f76b4c67df0a44922d0bac0f2fd30e4b8d0c97a301` | 178 × 14 | 0 |

Столбцы `data/iris.csv`: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`.

Столбцы `data/wine.csv`: `alcohol`, `malic_acid`, `ash`, `alcalinity_of_ash`, `magnesium`, `total_phenols`, `flavanoids`, `nonflavanoid_phenols`, `proanthocyanins`, `color_intensity`, `hue`, `od280/od315_of_diluted_wines`, `proline`, `target`.

### iris_features

| Файл | SHA-256 | Форма | Пропуски |
|---|---|---|---|
| `data/iris.csv` | `8228a6345ef84c613f21e4dca934ad87fc9d8629db248f215bdaf40bdb83c669` | 150 × 7 | 0 |

Столбцы `data/iris.csv`: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`, `sepal_area`, `petal_area`.

### merged

| Файл | SHA-256 | Форма | Пропуски |
|---|---|---|---|
| `data/iris.csv` | `8228a6345ef84c613f21e4dca934ad87fc9d8629db248f215bdaf40bdb83c669` | 150 × 7 | 0 |
| `data/wine.csv` | `b72adfd45219c12d4af882f76b4c67df0a44922d0bac0f2fd30e4b8d0c97a301` | 178 × 14 | 0 |

Столбцы `data/iris.csv`: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`, `sepal_area`, `petal_area`.

Столбцы `data/wine.csv`: `alcohol`, `malic_acid`, `ash`, `alcalinity_of_ash`, `magnesium`, `total_phenols`, `flavanoids`, `nonflavanoid_phenols`, `proanthocyanins`, `color_intensity`, `hue`, `od280/od315_of_diluted_wines`, `proline`, `target`.

### Ветвление, слияние и remote

`feature/wine` и `feature/iris-features` созданы от общей базы main. Первая добавляет Wine и сохраняет SHA-256 Iris; вторая изменяет Iris и не содержит Wine. Переключение обратно в main проверено после `dvc checkout`: Wine исчез, хэш Iris совпал с data-v1.

В `.gitattributes` сохранено `*.dvc merge=dvc`. В локальной конфигурации Git настроен `dvc git-hook merge-driver --ancestor %O --our %A --their %B`; новый clone должен настроить этот driver самостоятельно для будущих слияний.

DVC merge driver автоматически объединил оба состояния при git merge. Конфликта не возникло; после checkout итоговые SHA-256 Iris и Wine совпали с соответствующими ветками.

Родители merge-коммита: `f57a83d753ab5ff8b28ab5153ca55de5ae49411c d584f8acf48d56ef9845fffad13147e9df6aa8e8`. История обеих ветвей сохранена. main получила проверенный merge через fast-forward. Маркеры конфликта в data.dvc отсутствуют.

Remote `storage`: `C:/Users/Илья/.vscode/CODE/MLOPS/practice_3/dvc_remote_Gubeev`. Это соседняя директория вне репозитория. Безопасная конфигурация сохранена в `.dvc/config`. Все версии отправлены через dvc push; повторный push --all-commits не обнаружил недостающих объектов.

CSV не входят ни в один Git-коммит; cache и локальные настройки игнорируются. Файлы cache вручную не изменялись.

### Восстановление из чистого clone

Создан новый clone `C:/Users/Илья/.vscode/CODE/MLOPS/practice_3/mlops-data-Gubeev-clean-clone`. До dvc pull: data отсутствовала, локальный cache отсутствовал. Cache исходного репозитория не копировался и не использовался как shared cache.

После `dvc pull` контрольные суммы, размеры таблиц и столбцы совпали с итоговой версией. В той же чистой копии восстановлен `data-v1`, затем повторно получена итоговая `main`. Обе версии восстановились из remote без использования кэша исходного репозитория.

После проверки `dvc status --json` вернул `{}`, а `git status --short` не показал изменений.

| Файл | SHA-256 | Форма | Пропуски |
|---|---|---|---|
| `data/iris.csv` | `8228a6345ef84c613f21e4dca934ad87fc9d8629db248f215bdaf40bdb83c669` | 150 × 7 | 0 |
| `data/wine.csv` | `b72adfd45219c12d4af882f76b4c67df0a44922d0bac0f2fd30e4b8d0c97a301` | 178 × 14 | 0 |

Столбцы `data/iris.csv`: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`, `sepal_area`, `petal_area`.

Столбцы `data/wine.csv`: `alcohol`, `malic_acid`, `ash`, `alcalinity_of_ash`, `magnesium`, `total_phenols`, `flavanoids`, `nonflavanoid_phenols`, `proanthocyanins`, `color_intensity`, `hue`, `od280/od315_of_diluted_wines`, `proline`, `target`.

Локальный remote доступен только на этом компьютере. Для восстановления на другом компьютере нужно перенести remote отдельно или заменить его общим сетевым/S3-хранилищем; загрузка только Git-репозитория не передаёт CSV.

## ClearML Dataset

Project: `MIIT/MLOps/practice_3/Gubeev`. Dataset name: `sklearn-tabular-Gubeev`.

- `BASE_ID`: `77ab3b41f30a48a7b4da01a60e705aba`
- `WINE_ID`: `fd4384d1b03242269ec15a584a543499`
- `IRIS_FEATURES_ID`: `23306db43cc441fd8eb27f66502bf1a1`

Проверка выполнена 17.10.2026 12:50 (Москва). Все три версии имеют статус completed и получены строго по ID в отдельные пустые директории.

Скачивание выполнено с новым пустым SDK cache; файлы получены из ClearML storage. Вторая физическая машина не использовалась.

Граф зависимостей: идентификатор версии → идентификаторы родителей.

```json
{
  "77ab3b41f30a48a7b4da01a60e705aba": [],
  "fd4384d1b03242269ec15a584a543499": [
    "77ab3b41f30a48a7b4da01a60e705aba"
  ],
  "23306db43cc441fd8eb27f66502bf1a1": [
    "77ab3b41f30a48a7b4da01a60e705aba"
  ]
}
```

### Версия 1.0.0

ID: `77ab3b41f30a48a7b4da01a60e705aba`. Статус: `completed`. Parents: `[]`. Полный список: `['iris.csv']`.

Added: `['iris.csv']`; modified: `[]`; removed: `[]`.

Граф зависимостей:

```json
{
  "77ab3b41f30a48a7b4da01a60e705aba": []
}
```

| Файл | SHA-256 | Форма | Пропуски |
|---|---|---|---|
| `1.0.0/iris.csv` | `acb1d0e09be856a27d25798722572591b3ec55df2382354c5f83919f4b61e96b` | 150 × 5 | 0 |

Столбцы `1.0.0/iris.csv`: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`.

[Открыть версию 1.0.0 в ClearML](https://app.clear.ml/datasets/simple/afe5583bc96e401cbf4b48447e2a75f9/experiments/77ab3b41f30a48a7b4da01a60e705aba).

### Версия 1.1.0

ID: `fd4384d1b03242269ec15a584a543499`. Статус: `completed`. Parents: `['77ab3b41f30a48a7b4da01a60e705aba']`. Полный список: `['iris.csv', 'wine.csv']`.

Added: `['wine.csv']`; modified: `[]`; removed: `[]`.

Граф зависимостей:

```json
{
  "77ab3b41f30a48a7b4da01a60e705aba": [],
  "fd4384d1b03242269ec15a584a543499": [
    "77ab3b41f30a48a7b4da01a60e705aba"
  ]
}
```

| Файл | SHA-256 | Форма | Пропуски |
|---|---|---|---|
| `1.1.0/iris.csv` | `acb1d0e09be856a27d25798722572591b3ec55df2382354c5f83919f4b61e96b` | 150 × 5 | 0 |
| `1.1.0/wine.csv` | `b72adfd45219c12d4af882f76b4c67df0a44922d0bac0f2fd30e4b8d0c97a301` | 178 × 14 | 0 |

Столбцы `1.1.0/iris.csv`: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`.

Столбцы `1.1.0/wine.csv`: `alcohol`, `malic_acid`, `ash`, `alcalinity_of_ash`, `magnesium`, `total_phenols`, `flavanoids`, `nonflavanoid_phenols`, `proanthocyanins`, `color_intensity`, `hue`, `od280/od315_of_diluted_wines`, `proline`, `target`.

[Открыть версию 1.1.0 в ClearML](https://app.clear.ml/datasets/simple/afe5583bc96e401cbf4b48447e2a75f9/experiments/fd4384d1b03242269ec15a584a543499).

### Версия 2.0.0

ID: `23306db43cc441fd8eb27f66502bf1a1`. Статус: `completed`. Parents: `['77ab3b41f30a48a7b4da01a60e705aba']`. Полный список: `['iris.csv']`.

Added: `[]`; modified: `['iris.csv']`; removed: `[]`.

Граф зависимостей:

```json
{
  "23306db43cc441fd8eb27f66502bf1a1": [
    "77ab3b41f30a48a7b4da01a60e705aba"
  ]
}
```

| Файл | SHA-256 | Форма | Пропуски |
|---|---|---|---|
| `2.0.0/iris.csv` | `8228a6345ef84c613f21e4dca934ad87fc9d8629db248f215bdaf40bdb83c669` | 150 × 7 | 0 |

Столбцы `2.0.0/iris.csv`: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`, `sepal_area`, `petal_area`.

[Открыть версию 2.0.0 в ClearML](https://app.clear.ml/datasets/simple/afe5583bc96e401cbf4b48447e2a75f9/experiments/23306db43cc441fd8eb27f66502bf1a1).

База после создания обеих дочерних версий содержит только исходный iris.csv. WINE_ID отсутствует среди предков IRIS_FEATURES_ID. SHA-256 скачанных файлов совпадают с соответствующими версиями DVC.

## Сравнение

| Свойство | DVC: наблюдение в работе | ClearML Dataset |
|---|---|---|
| Идентификатор версии | В таблице записаны Git commit + directory MD5 и SHA-256 метафайла | Для 1.0.0, 1.1.0 и 2.0.0 записаны разные BASE_ID/WINE_ID/IRIS_FEATURES_ID |
| Метаданные | data.dvc и .dvc/config находятся в Git | Dataset.get по ID возвращает version, список файлов и граф родителей |
| Файлы | CSV в workspace, cache и соседнем remote; Git их не содержит | upload передавал по одному файлу; Wine наследует Iris от базы, что подтверждено составом и SHA-256 |
| Дочерняя версия | От базы созданы два Git-коммита в двух ветках | Обе версии созданы с parent_datasets=[BASE_ID]; parents проверены через SDK |
| Переключение | После switch main и checkout Wine исчез, Iris восстановился | Последовательное скачивание по трём ID дало три разных ожидаемых состава |
| Чистая машина | Clone без data/cache восстановлен через dvc pull из remote | Повторная проверка с новым пустым SDK cache; вторая физическая машина не использовалась |
| Ветвление | feature/wine и feature/iris-features имеют общую базу | graph[WINE_ID] и graph[IRIS_FEATURES_ID] равны [BASE_ID]; WINE_ID не предок 2.0.0 |
| Слияние | Merge driver объединил изменение Iris и добавление Wine; проверены оба SHA-256 | Слияние не выполнялось: обе дочерние версии скачаны и проверены независимо |
| Связь с Git | Версии data.dvc зафиксированы отдельными коммитами и data-v1 | Серверные ID, граф родителей и хэши сохранены в отчёте в Git |
| UI | В работе использованы CLI, git log и data.dvc | SDK вывел ссылки на страницы всех трёх Dataset; ссылки сохранены в отчёте, Web UI отдельно не проверялся |

## Ответы на вопросы

1. **Что определяет версию DVC?** Содержимое отслеживаемой директории задаётся content hash `.dir` в data.dvc, который ссылается на манифест с хэшами файлов. Git commit фиксирует конкретную редакцию этого метафайла и кода. SHA-256 метафайла полезен для проверки байтов; сам по себе он не является хэшем содержимого всех CSV. Разные коммиты могут ссылаться на одни данные.

2. **Почему коммита мало?** Git содержит указатель на объекты, но не CSV. Если cache утрачен и remote отсутствует, указанные объекты скачать неоткуда. В работе clone получил файлы именно из отдельного remote.

3. **Version и ID ClearML.** Version — задаваемый человеком семантический номер (1.0.0 и т.д.), ID — уникальная идентичность конкретного Dataset. Для восстановления скрипт использует ID; одинаковые подписи версии не заменяют идентификатор.

4. **Почему finalize не создаёт следующую версию?** finalize закрывает текущий Dataset для изменения. Следующая версия создаётся отдельным Dataset.create с новым ID и явными родителями.

5. **Как доказать происхождение 2.0.0?** В измеренном get_dependency_graph проверяют graph[IRIS_FEATURES_ID] == [BASE_ID], а WINE_ID отсутствует среди предков. Дополнительно состав 2.0.0 не содержит Wine. Один только состав файлов не доказывает lineage. Результат проверки сохранён в отчёте.

6. **Switch без DVC checkout.** Git изменит data.dvc, но CSV могут остаться от прежней ветки. Код будет читать состояние, не соответствующее Git; dvc status покажет расхождение. В работе workspace приводился к версии main явно через checkout.

7. **Где удобнее каждый инструмент?** DVC удобен для двух Git-веток и слияния независимых изменений Iris/Wine: история данных идёт вместе с кодом. ClearML Dataset удобен для выдачи финализированных версий по ID и просмотра родительского графа в общем сервере, без переключения Git. В работе это подтверждено независимым скачиванием трёх версий по ID и проверкой parents через SDK.

## Источники

- [DVC merge driver](https://dvc.org/doc/user-guide/how-to/resolve-merge-conflicts)

- [ClearML Dataset SDK](https://clear.ml/docs/latest/docs/references/sdk/dataset/)

Учебные материалы: `data_versioning_practice.md` и `explained.md`.

## Эксперименты

Wine получен из финализированной версии ClearML Dataset. Перед обучением проверен SHA-256 CSV. Все шесть конфигураций используют один стратифицированный split: 106 строк train, 36 validation и 36 test, random_state=42. Индексы строк и состав классов сохранены в split.json.

- Dataset ID: `fd4384d1b03242269ec15a584a543499`.
- SHA-256 Wine: `b72adfd45219c12d4af882f76b4c67df0a44922d0bac0f2fd30e4b8d0c97a301`.
- Tracking URI: `http://127.0.0.1:8081`.
- Experiment: `miit-mlops-practice-4-Gubeev`, ID `1`.
- Серия запусков: `f6ddb08de782434c`.
- SHA-256 split: `98c7de9ab336ea5b15d51090eb0f897ba517ec3a3670692762b03b628d1af745`.

| Компонент | Версия |
|---|---|
| Python | 3.12.10 |
| mlflow | 3.18.0 |
| clearml | 1.18.0 |
| scikit-learn | 1.6.1 |
| pandas | 2.2.3 |
| numpy | 2.5.4 |
| scipy | 1.17.1 |
| joblib | 1.6.0 |
| matplotlib | 3.11.2 |

### Сравнение конфигураций

| Run | Run ID | Семейство | Параметры | Validation F1 | Время обучения, с |
|---|---|---|---|---:|---:|
| rf-depth-6 | `4c3cff12b29e431d9bc795003e86a96c` | random_forest | `n_estimators=100, max_depth=6, random_state=42` | 0.972369 | 0.068131 |
| rf-depth-unlimited | `e76bcad75a944b88a450abf04d58d14d` | random_forest | `n_estimators=200, max_depth=None, random_state=42` | 0.972369 | 0.143181 |
| rf-depth-3 | `09b98b94ff25449fb1bc2d8ffcd6422a` | random_forest | `n_estimators=100, max_depth=3, random_state=42` | 0.944833 | 0.102185 |
| logreg-c-0.1 | `0c6acbee35a14bb394c57cab0d2edebc` | logistic_regression | `C=0.1, solver=lbfgs, max_iter=1000, random_state=42` | 0.943525 | 0.019451 |
| logreg-c-1 | `2a26a4e89605431ca9fe378620acdd44` | logistic_regression | `C=1.0, solver=lbfgs, max_iter=1000, random_state=42` | 0.943525 | 0.008564 |
| logreg-c-10 | `b2c18d715d3b42879c651f6bcdb39590` | logistic_regression | `C=10.0, solver=lbfgs, max_iter=1000, random_state=42` | 0.914747 | 0.010551 |

Выбрана конфигурация **rf-depth-6**: максимальный validation F1 0.972369. При равенстве F1 применяется алфавитный порядок имён запусков. Test не использовался при выборе конфигурации.

Лучший MLflow run ID: `4c3cff12b29e431d9bc795003e86a96c`. Модель загружена по `runs:/4c3cff12b29e431d9bc795003e86a96c/model`; её предсказания совпали с исходным Pipeline. Проверены обязательные поля всех шести runs, signature и пять строк input example. Результаты сохранены в verification.json.

### Итоговая оценка

| Метрика test | Значение |
|---|---:|
| accuracy | 0.944444 |
| precision_weighted | 0.944444 |
| recall_weighted | 0.944444 |
| f1_weighted | 0.944444 |

Метрики test вычислены один раз после выбора победителя и записаны только в его run с префиксом test_. Матрица ошибок, предсказания и показатели по классам сохранены как MLflow artifacts.

### Результат в ClearML

- Task: [4bd27f0a960347528a048fc8bb9c1b35](https://app.clear.ml/projects/66706abda484440e8133babbfd2e204c/experiments/4bd27f0a960347528a048fc8bb9c1b35), статус `completed`.
- Model: [80b21625d99d4852a1eef58058751a8d](https://app.clear.ml/projects/66706abda484440e8133babbfd2e204c/models/80b21625d99d4852a1eef58058751a8d), опубликована.
- В Task загружены параметры победителя, validation/test-метрики, таблица сравнения, verification.json, модель, split, окружение и матрица ошибок.
- Метаданные модели содержат MLflow run ID, Dataset ID и хэши. Файл модели повторно скачан из ClearML, SHA-256 совпал с локальным.

### Ссылки на Task и версии данных

| Результат | ClearML |
|---|---|
| Лучшая модель Wine — практика 4 | [Открыть](https://app.clear.ml/projects/66706abda484440e8133babbfd2e204c/tasks/4bd27f0a960347528a048fc8bb9c1b35/execution?columns=selected&columns=type&columns=name&columns=tags&columns=status&columns=project.name&columns=users&columns=started&columns=last_update&columns=last_iteration&columns=parent.name&order=-last_update) |
| Iris — базовая версия 1.0.0 | [Открыть](https://app.clear.ml/projects/afe5583bc96e401cbf4b48447e2a75f9/tasks/77ab3b41f30a48a7b4da01a60e705aba/execution?columns=selected&columns=type&columns=name&columns=tags&columns=status&columns=project.name&columns=users&columns=started&columns=last_update&columns=last_iteration&columns=parent.name&order=-last_update) |
| Iris + Wine — версия 1.1.0 | [Открыть](https://app.clear.ml/projects/afe5583bc96e401cbf4b48447e2a75f9/tasks/fd4384d1b03242269ec15a584a543499/execution?columns=selected&columns=type&columns=name&columns=tags&columns=status&columns=project.name&columns=users&columns=started&columns=last_update&columns=last_iteration&columns=parent.name&order=-last_update) |
| Iris с дополнительными признаками — версия 2.0.0 | [Открыть](https://app.clear.ml/projects/afe5583bc96e401cbf4b48447e2a75f9/tasks/23306db43cc441fd8eb27f66502bf1a1/execution?columns=selected&columns=type&columns=name&columns=tags&columns=status&columns=project.name&columns=users&columns=started&columns=last_update&columns=last_iteration&columns=parent.name&order=-last_update) |

Ссылки также сохранены в [sharing_links.json](sharing_links.json). Просмотр из другого workspace требует созданной ссылки чтения через Share → Create link и входа в ClearML. Этот порядок описан в [документации ClearML](https://clear.ml/docs/latest/docs/webapp/webapp_exp_sharing/). Доступ из другого workspace отдельно не проверялся.

### Воспроизведение

```powershell
poetry install
clearml-init
poetry run python run_experiments.py `
  --dataset-id fd4384d1b03242269ec15a584a543499 `
  --expected-sha256 b72adfd45219c12d4af882f76b4c67df0a44922d0bac0f2fd30e4b8d0c97a301 `
  --tracking-uri http://127.0.0.1:8081 --clearml --update-report
```

Перед запуском HTTP-варианта нужно поднять MLflow Tracking Server по команде из README. Для работы без сервера можно передать --tracking-uri sqlite:///mlflow.db. Повторное выполнение создаёт новую серию из шести runs в том же experiment.

### Дополнительные проверки

Автоматические тесты проверяют структуру записанных runs и изоляцию test-метрик. Сохранены confusion_matrix.png и classification_report.json. Tracking Server использует SQLite для метаданных и отдельное файловое хранилище артефактов.

В этой серии время обучения составило от 0.008564 до 0.143181 с. Эти измерения относятся к одному запуску на данном компьютере; небольшую разницу времени нельзя считать устойчивым преимуществом. Качество сравнивалось по validation F1, скорость приведена отдельно.

### Анализ качества и времени

Logistic Regression с C=0.1 и C=1 дала одинаковый validation F1 0.943525. При C=10 он снизился до 0.914747: ослабление регуляризации в этой серии не улучшило качество.

У Random Forest увеличение глубины с 3 до 6 повысило validation F1 с 0.944833 до 0.972369. Вариант с 200 деревьями без ограничения глубины получил тот же F1, что и 100 деревьев с глубиной 6. В этой серии его обучение заняло 0.143181 с против 0.068131 с у выбранной конфигурации. Поэтому усложнение леса здесь не дало выигрыша по validation; разовое измерение времени не является общим сравнением производительности.

На test выбранная модель правильно классифицировала 34 из 36 объектов. Две ошибки приходятся на классы 0 и 1; все 10 объектов класса 2 распознаны верно. Итоговый test F1 0.944444 ниже validation F1 0.972369. Test использован для итоговой оценки, параметры по его результатам не менялись.

### Проверка проекта и повторного запуска

Все 6 автоматических тестов прошли. Проверки `python -m pip check` и `poetry check --lock` завершились без ошибок. Итог проверок сохранён в [validation_summary.json](validation_summary.json).

Повторное выполнение создало ещё шесть runs в experiment ID 1. Совпали SHA-256 кода, split, все validation F1, выбранная конфигурация и test-метрики. Исходная серия: `f6ddb08de782434c`, повторная: `703d99d788874b99`. Результаты проверки — [reproducibility.json](reproducibility.json).

Код выполненной серии: commit `12ba94d0c39f939bd62364727260ffc4c07425ce`, SHA-256 `67396bdd4dd7f99f3cf836196a2474044f5870256539f4e7a28cca6db91a86ef`.

Демонстрационный [experiments_demo.ipynb](notebooks/experiments_demo.ipynb) выполнен отдельно: 9 ячеек с кодом, ошибок нет. Демонстрация использует Breast Cancer; её результаты не включены в сравнение Wine.
