# Практическая работа №3. Версионирование данных с DVC и ClearML

Автор: Gubeev. Дата локального выполнения: 14.10.2026.

## Статус выполнения

DVC выполнен и проверен. ClearML пока не выполнен: учебный сервер и аккаунт не предоставлены, SDK не настроен. Скрипт подготовлен; Dataset IDs и наблюдения сервера не подменяются ожидаемыми результатами. Работа до завершения этой части не готова к полной сдаче.

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

Локальный Git-репозиторий: [mlops-data-Gubeev](C:/Users/Илья/.vscode/CODE/MLOPS/practice_3/mlops-data-Gubeev). Основная ветка — `main`. Публичный URL пока отсутствует; после загрузки репозитория в Git-хостинг его следует добавить в этот раздел.

## Подготовка и проверка таблиц

`prepare_data.py` сортирует строки по всем исходным признакам и target (mergesort), сохраняет исходный порядок столбцов, UTF-8, LF, без индекса, `float_format="%.17g"`. Новые признаки добавляются последними. Каждый режим перезаписывает только свой CSV, поэтому для состояния base используется пустая папка либо DVC checkout базовой версии.

`check_data.py` проверяет точный состав выбранной версии, порядок столбцов, отсутствие индекса и пропусков, число строк, все исходные значения и target, порядок строк и формулы площадей. Для вещественных значений допускается ошибка 1e-12.

Проверки генератора и валидатора: все три режима повторяют одинаковые байты и сохраняют соседний файл; валидатор отклоняет: неверная площадь; валидатор отклоняет: изменённый target; валидатор отклоняет: потерянная строка; валидатор отклоняет: неверный порядок столбцов; валидатор отклоняет: индекс pandas; валидатор отклоняет: пропущенное значение; валидатор отклоняет отсутствующий файл; git switch без checkout оставлял Wine предыдущей ветки в workspace.

## Версии DVC

| Состояние | Git commit | Tag/ветка при создании | DVC directory MD5 | SHA-256 data.dvc |
|---|---|---|---|---|
| base | `1e91d10efc3bb56147037f5cefd37575916902c3` | `data-v1` | `68694d6e2fc4bf7a7da11d2b0d489e1e.dir` | `3aa2128aa15e4da33d4f63faa9c38edb24d1b02d1cab7cb8eb3d1c5d10bc596b` |
| wine | `7e806b22116f06bbdaf7e14545780829571cacec` | `feature/wine` | `cd692bf1d9bad578ff6e9bdaf5fff033.dir` | `1363389a0a3865e646f3d2b8cb1e71bd518af1f5fa21971272b77365e25e57df` |
| iris_features | `cbe9f4edbfd0061dacee5b3b8bbfe2f4cf8df091` | `feature/iris-features before merge (data-merged^1)` | `84fad98472f78577bceb6d442c1f794d.dir` | `c2574a6022983aaaeedd6a3722cfd498fb901e2434a1af930b258f883c266697` |
| merged | `c6a18cf11c2dc94f3e5939b23d6d5381873ce5e1` | `main; data-merged` | `d23e2a33f1aa86af524072021da153ed.dir` | `53ae84294d6d0310b6dedf66e175c94afae61db8a05f6e7b226f0d591a289cb8` |

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

Родители merge-коммита: `cbe9f4edbfd0061dacee5b3b8bbfe2f4cf8df091 7e806b22116f06bbdaf7e14545780829571cacec`. История обеих ветвей сохранена. main получила проверенный merge через fast-forward. Маркеры конфликта в data.dvc отсутствуют.

Remote `storage`: `C:/Users/Илья/.vscode/CODE/MLOPS/practice_3/dvc_remote_Gubeev`. Это соседняя директория вне репозитория. Безопасная конфигурация сохранена в `.dvc/config`. Все версии отправлены через dvc push; повторный push --all-commits не обнаружил недостающих объектов.

CSV не входят ни в один Git-коммит; cache и локальные настройки игнорируются. Файлы cache вручную не изменялись.

### Восстановление из чистого clone

Создан новый clone `C:/Users/Илья/.vscode/CODE/MLOPS/practice_3/mlops-data-Gubeev-clean-clone`. До dvc pull: data отсутствовала, локальный cache отсутствовал. Cache исходного репозитория не копировался и не использовался как shared cache.

После dvc pull SHA-256, формы и столбцы совпали с итоговым состоянием. Дополнительно data-v1 восстановлен из remote в том же clone, затем итоговая main получена снова. Это проверяет доступность базовой и итоговой версий независимо от старого cache.

Итоговый `dvc status --json`: `{}`. `git status --short`: пустой после сохранения отчёта.

| Файл | SHA-256 | Форма | Пропуски |
|---|---|---|---|
| `data/iris.csv` | `8228a6345ef84c613f21e4dca934ad87fc9d8629db248f215bdaf40bdb83c669` | 150 × 7 | 0 |
| `data/wine.csv` | `b72adfd45219c12d4af882f76b4c67df0a44922d0bac0f2fd30e4b8d0c97a301` | 178 × 14 | 0 |

Столбцы `data/iris.csv`: `sepal length (cm)`, `sepal width (cm)`, `petal length (cm)`, `petal width (cm)`, `target`, `sepal_area`, `petal_area`.

Столбцы `data/wine.csv`: `alcohol`, `malic_acid`, `ash`, `alcalinity_of_ash`, `magnesium`, `total_phenols`, `flavanoids`, `nonflavanoid_phenols`, `proanthocyanins`, `color_intensity`, `hue`, `od280/od315_of_diluted_wines`, `proline`, `target`.

Локальный remote доступен только на этом компьютере. Для восстановления на другом компьютере нужно перенести remote отдельно или заменить его общим сетевым/S3-хранилищем; загрузка только Git-репозитория не передаёт CSV.

## ClearML Dataset

`BASE_ID`, `WINE_ID`, `IRIS_FEATURES_ID`: **ещё не получены**. Реальные dependency graph, статус Completed, состав и SHA-256 скачанных версий будут автоматически добавлены после успешного запуска `clearml_versions.py`.

Подготовленная схема (ожидаемая, не измеренный граф сервера):
```text
1.0.0 (BASE_ID): iris.csv
├── 1.1.0 (WINE_ID): исходный iris.csv + wine.csv
└── 2.0.0 (IRIS_FEATURES_ID): iris.csv с двумя площадями, без wine.csv
```

Скрипт создаёт обе дочерние версии с единственным parent BASE_ID, добавляет в 1.1.0 только wine.csv, в 2.0.0 только изменённый iris.csv; вызывает upload до finalize. Затем получает каждую версию по ID, проверяет parents, added/modified/removed, полный состав и локальные хэши. ID сохраняются сразу после создания, поэтому повторный запуск продолжает работу с теми же объектами.

Инструкция настройки и запуска находится в README.md. Credentials не записаны в код, Git или отчёт.

## Сравнение

ClearML ниже описан по подготовленному коду и SDK; наблюдения сервера пока отсутствуют.

| Свойство | DVC: наблюдение в работе | ClearML Dataset |
|---|---|---|
| Идентификатор версии | В таблице записаны Git commit + directory MD5 и SHA-256 метафайла | Точные BASE_ID/WINE_ID/IRIS_FEATURES_ID; номер версии задаётся отдельно |
| Метаданные | data.dvc и .dvc/config находятся в Git | Dataset на сервере, SDK получает его по ID |
| Файлы | CSV в workspace, cache и соседнем remote; Git их не содержит | upload отправляет новые/изменённые файлы в configured storage; дочерняя версия наследует Iris |
| Дочерняя версия | От базы созданы два Git-коммита в двух ветках | Dataset.create с явным parent_datasets=[BASE_ID] |
| Переключение | После switch main и checkout Wine исчез, Iris восстановился | Dataset.get(dataset_id=...) и отдельная локальная копия каждой версии |
| Чистая машина | Clone без data/cache восстановлен через dvc pull из remote | Нужны SDK, credentials, доступ к server/storage; get по ID и download |
| Ветвление | feature/wine и feature/iris-features имеют общую базу | 1.1.0 и 2.0.0 явно наследуют одну базу |
| Слияние | Merge driver объединил изменение Iris и добавление Wine; проверены оба SHA-256 | Слияние в этой части задания не выполняется; SDK допускает несколько parents |
| Связь с Git | Версии data.dvc зафиксированы отдельными коммитами и data-v1 | Git хранит код и ID в отчёте; Dataset ID существует независимо от Git |
| UI | В работе использованы CLI, git log и data.dvc | Проверка Web UI пока не выполнена; SDK проверяет финализацию и lineage |

## Ответы на вопросы

1. **Что определяет версию DVC?** Содержимое отслеживаемой директории задаётся content hash `.dir` в data.dvc, который ссылается на манифест с хэшами файлов. Git commit фиксирует конкретную редакцию этого метафайла и кода. SHA-256 метафайла полезен для проверки байтов; сам по себе он не является хэшем содержимого всех CSV. Разные коммиты могут ссылаться на одни данные.

2. **Почему коммита мало?** Git содержит указатель на объекты, но не CSV. Если cache утрачен и remote отсутствует, указанные объекты скачать неоткуда. В работе clone получил файлы именно из отдельного remote.

3. **Version и ID ClearML.** Version — задаваемый человеком семантический номер (1.0.0 и т.д.), ID — уникальная идентичность конкретного Dataset. Для восстановления скрипт использует ID; одинаковые подписи версии не заменяют идентификатор.

4. **Почему finalize не создаёт следующую версию?** finalize закрывает текущий Dataset для изменения. Следующая версия создаётся отдельным Dataset.create с новым ID и явными родителями.

5. **Как доказать происхождение 2.0.0?** В измеренном get_dependency_graph проверяют graph[IRIS_FEATURES_ID] == [BASE_ID], а WINE_ID отсутствует среди предков. Дополнительно состав 2.0.0 не содержит Wine. Один только состав файлов не доказывает lineage. Сейчас эта проверка реализована в скрипте, но до подключения к серверу не выполнена.

6. **Switch без DVC checkout.** Git изменит data.dvc, но CSV могут остаться от прежней ветки. Код будет читать состояние, не соответствующее Git; dvc status покажет расхождение. В работе workspace приводился к версии main явно через checkout.

7. **Где удобнее каждый инструмент?** DVC удобен для двух Git-веток и слияния независимых изменений Iris/Wine: история данных идёт вместе с кодом. ClearML Dataset удобен для выдачи финализированных версий по ID и просмотра родительского графа в общем сервере, без переключения Git. Сравнение удобства ClearML пока основано на подготовленном сценарии, а не на выполненной серверной части.

## Источники

- [DVC merge driver](https://dvc.org/doc/user-guide/how-to/resolve-merge-conflicts)

- [ClearML Dataset SDK](https://clear.ml/docs/latest/docs/references/sdk/dataset/)

Исходное задание: data_versioning_practice.md; справочник: explained.md. Демонстрационный notebook выполнялся отдельно и не использован вместо самостоятельного решения. Выполненная копия dvc_clearml_sklearn_demo.executed.ipynb адаптирует URL локального remote на относительный путь для кириллицы в Windows; исходный файл сохранён без изменений. Локальные ячейки демонстрации и practice_3_solution.ipynb выполнены без ошибок. ClearML-ячейки демонстрации пропущены (run_clearml=False).
