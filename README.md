# MLOps, практика 3 — Gubeev

Самостоятельный сценарий с Iris/Wine. Фактические результаты и оставшиеся шаги — в `REPORT.md`; проверяемые записи — в `evidence/`.

Исходный демонстрационный notebook сохранён без изменений. Локальные ячейки демонстрации были выполнены без ошибок; ClearML-ячейки пропущены согласно исходной настройке `run_clearml=False`. При запуске URL локального DVC remote заменялся относительным путём для совместимости с кириллицей в Windows. Выполненная копия демонстрации и её временные папки удалены после проверки. Выполненный notebook самостоятельного решения — `practice_3_solution.ipynb`.

## Окружение

Требуется Python 3.12 и Git. Установите Poetry 2.1.1, затем из этой папки:

```powershell
poetry install
poetry run python check_data.py --version merged
```

В текущей рабочей папке уже подготовлено окружение `../.venv`. Для него:

```powershell
..\.venv\Scripts\Activate.ps1
python check_data.py --version merged
```

Откройте `practice_3_solution.ipynb` и выберите Python из `practice_3/.venv/Scripts/python.exe`. Ноутбук проверяет готовые результаты; повторное выполнение не создаёт новый Git-репозиторий и не переключает рабочие ветки.

## Восстановление DVC

Клонируйте репозиторий, затем из его папки выполните `poetry install` и `poetry run dvc pull`. Локальный remote — соседняя папка `../dvc_remote_Gubeev`. Она уже создана вне репозитория и содержит все версии. На другом компьютере нужен отдельный доступ к этому хранилищу; один Git clone не переносит объекты данных.

```powershell
poetry run dvc pull
poetry run python check_data.py --version merged
git switch --detach data-v1
poetry run dvc checkout
poetry run python check_data.py --version base
git switch main
poetry run dvc checkout
```

Git merge driver настраивается локально и не переносится через clone:

```powershell
git config merge.dvc.name "DVC merge driver"
git config merge.dvc.driver "dvc git-hook merge-driver --ancestor %O --our %A --their %B"
```

Для merge команда `dvc` должна быть доступна в PATH (например, внутри активированного Poetry-окружения). Атрибут `*.dvc merge=dvc` уже сохранён в `.gitattributes`.

Порядок выполненного сценария: base → tag data-v1 → feature/wine → возврат main и dvc checkout → feature/iris-features → merge feature/wine → проверка → main → чистый clone и dvc pull. Хэши каждого этапа сохранены в отчёте.

## ClearML

В аккаунте ClearML Hosted Service созданы и проверены версии `1.0.0`, `1.1.0`, `2.0.0` проекта `MIIT/MLOps/practice_3/Gubeev`, Dataset `sklearn-tabular-Gubeev`. Точные ID, ссылки на страницы, статусы, состав и хэши скачанных файлов находятся в `REPORT.md` и `evidence/clearml.json`.

На этом компьютере SDK уже настроен. На новом компьютере получите собственные credentials в Settings → Workspace → Create new credentials и выполните в активированном окружении:

```powershell
clearml-init
```

Вставляйте предложенную сервером конфигурацию только в интерактивную настройку. Пользовательский `clearml.conf` должен находиться вне Git. В чат и ноутбук ключи копировать не нужно.

Скрипт без флага `--execute` показывает план. Команда создания или продолжения прерванного запуска:

```powershell
python clearml_versions.py
python clearml_versions.py --execute --expected-api-host https://api.clear.ml
```

Обе дочерние версии наследуют базу; неизменённый Iris повторно не добавляется в Wine. Скрипт не удаляет серверные Dataset. Если ID уже сохранены, используются существующие объекты, новые версии повторно не создаются.

При создании каждый ID сразу сохраняется в игнорируемый `clearml_ids.local.json`, чтобы продолжить работу после частичного сбоя. После успешного скачивания ID и результаты сохраняются в `evidence/clearml.json`, откуда скрипт тоже умеет читать ID. Поэтому после завершения проверки локальный файл IDs можно удалить. `REPORT.md` автоматически обновляется реальными результатами.

Повторная проверка уже созданных объектов:

```powershell
python clearml_versions.py --execute --inspect-only --fresh-cache --expected-api-host https://api.clear.ml
git add evidence/clearml.json REPORT.md
git commit -m "Record verified ClearML dataset versions"
```

Временные исходные CSV, скачанные копии и SDK cache помещаются в игнорируемую `.dvc/tmp/clearml/`. Флаг `--fresh-cache` создаёт новый пустой cache, чтобы проверить доступность файлов в storage. После проверки временные данные удалены, результаты сохранены в `evidence/clearml.json`. Для независимого восстановления на другой машине нужны репозиторий с этим JSON, те же зависимости и настроенный SDK с доступом к Dataset.

## Сдача

Сдавайте отслеживаемые Git файлы, включая `.dvc/config`, `.dvcignore`, `data.dvc`, скрипты, `pyproject.toml`, `poetry.lock`, `REPORT.md`. Данные, cache, remote, credentials, окружение и скачанные копии не включаются. Git history сохранена в репозитории. После настройки Git-хостинга добавьте его URL в отчёт и отправьте `main`, обе feature-ветки и tags.

Проверочный clone, временные файлы установки, демонстрационные папки и дублирующие архивы удалены после проверки. В рабочей папке оставлены исходные материалы, этот репозиторий, окружение `../.venv` и хранилище `../dvc_remote_Gubeev`.

При необходимости создайте архив для сдачи и резервную копию Git history:

```powershell
git archive --format=zip --prefix=mlops-data-Gubeev/ --output=../mlops-data-Gubeev-submission.zip HEAD
git bundle create ../mlops-data-Gubeev.bundle --all
```
