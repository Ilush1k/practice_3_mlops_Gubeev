# MLOps, практика 3 — Gubeev

Самостоятельный сценарий с Iris/Wine. Фактические результаты и оставшиеся шаги — в `REPORT.md`; проверяемые записи — в `evidence/`.

Исходный демонстрационный notebook сохранён без изменений. Его выполненная копия находится рядом с этим репозиторием: `../dvc_clearml_sklearn_demo.executed.ipynb`. В копии URL локального DVC remote заменён относительным путём, поскольку DVC 3.59.2 не сохраняет абсолютный Windows-путь с кириллицей. Локальные ячейки выполнены без ошибок; ClearML-ячейки пропущены согласно исходной настройке `run_clearml=False`.

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

## Завершение ClearML

Адрес сервера в исходном задании не указан. Узнайте у преподавателя учебный server; если допускается личный аккаунт, можно использовать [ClearML Hosted Service](https://app.clear.ml/). В UI откройте Settings → Workspace → Create new credentials. В активированном окружении выполните:

```powershell
clearml-init
```

Вставляйте предложенную сервером конфигурацию только в интерактивную настройку. Пользовательский `clearml.conf` должен находиться вне Git. В чат и ноутбук ключи копировать не нужно.

Скрипт без флага `--execute` показывает план. Для создания замените `<API URL>` настоящим API-адресом из настройки (он может отличаться от Web UI):

```powershell
python clearml_versions.py
python clearml_versions.py --execute --expected-api-host <API URL>
```

Создаются `MIIT/MLOps/practice_3/Gubeev` / `sklearn-tabular-Gubeev`, версии `1.0.0`, `1.1.0`, `2.0.0`. Дочерние версии обе наследуют базу; неизменённый Iris повторно не добавляется в Wine. Скрипт не удаляет серверные Dataset.

Каждый ID сразу сохраняется в игнорируемый `clearml_ids.local.json`. При частичном сбое повторите ту же команду: существующие объекты используются снова. Не удаляйте этот файл до завершения проверки. После успешного скачивания скрипт создаёт `evidence/clearml.json` и обновляет `REPORT.md` реальными ID, lineage, хэшами и составом.

Повторная проверка уже созданных объектов:

```powershell
python clearml_versions.py --execute --inspect-only --expected-api-host <API URL>
git add evidence/clearml.json REPORT.md
git commit -m "Record verified ClearML dataset versions"
```

Скачанные копии находятся в игнорируемой `clearml_downloads/`, исходные временные таблицы — в `clearml_sources/`. Для независимого восстановления можно перенести JSON с тремя ID на другую машину и выполнить `--inspect-only` с теми же зависимостями и настроенным SDK.

## Сдача

Сдавайте отслеживаемые Git файлы, включая `.dvc/config`, `.dvcignore`, `data.dvc`, скрипты, `pyproject.toml`, `poetry.lock`, `REPORT.md`. Данные, cache, remote, credentials, окружение и скачанные копии не включаются. Git history сохранена в репозитории и отдельном bundle рядом с ним. После настройки Git-хостинга добавьте его URL в отчёт и отправьте `main`, обе feature-ветки и tags.

Архив рядом с проектом содержит локальный результат **до выполнения ClearML**. После завершения серверной части пересоберите его:

```powershell
git archive --format=zip --prefix=mlops-data-Gubeev/ --output=../mlops-data-Gubeev-submission.zip HEAD
git bundle create ../mlops-data-Gubeev.bundle --all
```
