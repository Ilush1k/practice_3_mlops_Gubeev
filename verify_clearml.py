"""Проверить IDs, parents, Completed, состав и SHA-256 скачанных ClearML versions."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from check_data import check_data
from clearml_versions import (API_HOST, BASE_ID, EXPECTED_SHA256, IRIS_FEATURES_ID,
                              NAME, PROJECT, ROOT, SPECS, WINE_ID, get_dataset,
                              inspect_dataset, setup_sdk)
from download_clearml_versions import download_versions, latest_download


def verify_downloads(directory: Path) -> dict[str, list[dict]]:
    """Локальная проверка таблиц, включая совпадение байтов с версиями DVC."""
    result = {}
    for mode, spec in SPECS.items():
        tables = check_data(directory / spec["version"], mode)
        hashes = {Path(row["path"]).name: row["sha256"] for row in tables}
        if hashes != EXPECTED_SHA256[mode]:
            raise ValueError(f"{spec['version']}: SHA-256 не совпадает с проверенной версией DVC")
        result[mode] = tables
    return result


def update_report(versions: list[dict], *, fresh_cache: bool) -> None:
    """Обновить только ClearML-раздел, сохранив наблюдения DVC."""
    report = ROOT / "REPORT.md"
    text = report.read_text(encoding="utf-8")
    start = text.index("## ClearML Dataset")
    end = text.index("## Сравнение", start)
    graph = {}
    for version in versions:
        graph.update(version["graph"])
    lines = ["## ClearML Dataset", f"Project: `{PROJECT}`. Dataset name: `{NAME}`.",
             f"- `BASE_ID`: `{BASE_ID}`\n- `WINE_ID`: `{WINE_ID}`\n- `IRIS_FEATURES_ID`: `{IRIS_FEATURES_ID}`",
             f"Проверка выполнена {datetime.now(ZoneInfo('Europe/Moscow')):%d.%m.%Y %H:%M} (Москва). Все три версии имеют статус completed и получены строго по ID в отдельные пустые директории.",
             "Скачивание выполнено с новым пустым SDK cache; файлы получены из ClearML storage. Вторая физическая машина не использовалась." if fresh_cache else
             "Проверены скачанные копии и серверные метаданные. SDK cache мог использоваться повторно.",
             "Общий измеренный dependency graph (ID версии → IDs родителей):\n```json\n" + json.dumps(graph, indent=2) + "\n```"]
    for version in versions:
        lines.extend([f"### Version {version['version']}",
                      f"ID: `{version['id']}`. Статус: `{version['status']}`. Parents: `{version['parents']}`. Полный список: `{version['files']}`.",
                      f"Added: `{version['changes']['added']}`; modified: `{version['changes']['modified']}`; removed: `{version['changes']['removed']}`.",
                      "Dependency graph:\n```json\n" + json.dumps(version["graph"], indent=2) + "\n```",
                      "| Файл | SHA-256 | Форма | Пропуски |\n|---|---|---|---|\n" + "\n".join(
                          f"| `{row['path']}` | `{row['sha256']}` | {row['rows']} × {row['column_count']} | {row['missing_values']} |" for row in version["tables"])])
        for row in version["tables"]:
            lines.append(f"Столбцы `{row['path']}`: " + ", ".join(f"`{column}`" for column in row["columns"]) + ".")
        lines.append(f"[Открыть version {version['version']} в ClearML]({version['dataset_url']}).")
    lines.append("База после создания обеих дочерних версий содержит только исходный iris.csv. WINE_ID отсутствует среди предков IRIS_FEATURES_ID. SHA-256 скачанных файлов совпадают с соответствующими версиями DVC.")
    with report.open("w", encoding="utf-8", newline="\n") as target:
        target.write(text[:start] + "\n\n".join(lines) + "\n\n" + text[end:])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", type=Path, help="Каталог с подкаталогами 1.0.0, 1.1.0 и 2.0.0")
    parser.add_argument("--fresh-cache", action="store_true", help="Повторно скачать все версии с пустым cache")
    parser.add_argument("--update-report", action="store_true")
    parser.add_argument("--expected-api-host", default=API_HOST)
    args = parser.parse_args()
    if args.downloads and args.fresh_cache:
        parser.error("Выберите --downloads или --fresh-cache")
    directory = args.downloads or (None if args.fresh_cache else latest_download())
    downloaded_now = directory is None
    if downloaded_now:
        directory = download_versions(fresh_cache=True, expected_api_host=args.expected_api_host)
    else:
        setup_sdk(args.expected_api_host)
    tables = verify_downloads(directory)
    versions = []
    for mode in SPECS:
        result = inspect_dataset(get_dataset(mode), mode)
        result["tables"] = tables[mode]
        versions.append(result)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    if args.update_report:
        update_report(versions, fresh_cache=downloaded_now)
        print("REPORT.md обновлён")
    print("Все три версии, lineage и SHA-256 проверены")


if __name__ == "__main__":
    main()
