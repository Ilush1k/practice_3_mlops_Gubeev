"""Создать три версии на настроенном ClearML server и проверить скачивание по ID."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from check_data import check_data
from prepare_data import prepare

PROJECT = "MIIT/MLOps/practice_3/Gubeev"
NAME = "sklearn-tabular-Gubeev"
SPECS = [("BASE_ID", "1.0.0", "base"), ("WINE_ID", "1.1.0", "wine"),
         ("IRIS_FEATURES_ID", "2.0.0", "iris_features")]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Создать реальные Dataset на сервере")
    parser.add_argument("--inspect-only", action="store_true", help="Повторно скачать уже сохранённые ID")
    parser.add_argument("--expected-api-host", help="Адрес API, который должен совпасть с настройкой SDK")
    args = parser.parse_args()
    if not args.execute:
        print(f"Проект: {PROJECT}\nDataset: {NAME}\nВерсии: 1.0.0 → 1.1.0 и 1.0.0 → 2.0.0")
        print("Настройте clearml-init вне Git. Затем: python clearml_versions.py --execute --expected-api-host <API URL>")
        return
    if not args.expected_api_host:
        parser.error("Укажите --expected-api-host для проверки подключения к нужному серверу")

    from clearml import Dataset
    from clearml.backend_api.session import Session

    session = Session()
    actual_host = session.get_api_server_host().rstrip("/")
    if actual_host != args.expected_api_host.rstrip("/"):
        raise RuntimeError("Адрес API в настройке SDK не совпадает с --expected-api-host")
    root = Path(__file__).resolve().parent
    ids_path = root / "clearml_ids.local.json"
    ids = json.loads(ids_path.read_text(encoding="utf-8")) if ids_path.exists() else {}
    evidence_path = root / "evidence" / "clearml.json"
    evidence_path.parent.mkdir(exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    sources = root / "clearml_sources" / run_id
    versions = []
    for key, version, mode in SPECS:
        parents = [] if key == "BASE_ID" else [ids["BASE_ID"]]
        if key in ids:
            dataset = Dataset.get(dataset_id=ids[key])
        else:
            if args.inspect_only:
                raise RuntimeError(f"В {ids_path.name} отсутствует {key}")
            dataset = Dataset.create(
                dataset_project=PROJECT, dataset_name=NAME, dataset_version=version,
                parent_datasets=parents or None,
                dataset_tags=["practice_3", "Gubeev", "base" if key == "BASE_ID" else mode],
                description={"base": "Исходный Iris scikit-learn, без Wine и вычисляемых признаков",
                             "wine": "Наследование исходного Iris от базы; добавлен только Wine",
                             "iris_features": "Отдельная ветвь от базы: Iris с sepal_area и petal_area, без Wine"}[mode],
            )
            ids[key] = dataset.id
            ids_path.write_text(json.dumps(ids, indent=2), encoding="utf-8")
        if dataset.version != version:
            raise RuntimeError(f"Неверный номер версии сохранённого {key}")
        graph = dataset.get_dependency_graph()
        if graph.get(dataset.id, []) != parents:
            raise RuntimeError(f"Неверные родители {key}: {graph}")
        if not dataset.is_final():
            if args.inspect_only:
                raise RuntimeError(f"{key} ещё не финализирован")
            source = prepare(mode, sources / mode)
            dataset.add_files(path=str(source))
            dataset.upload()
            if not dataset.finalize():
                raise RuntimeError(f"Не удалось финализировать {key}")
        downloaded = Dataset.get(dataset_id=ids[key], only_completed=True)
        target = root / "clearml_downloads" / run_id / version
        downloaded.get_mutable_local_copy(target_folder=str(target), overwrite=False)
        summary = check_data(target, mode)
        expected = sources / f"expected_{mode}"
        prepare("iris_features" if mode == "iris_features" else "base", expected)
        if mode == "wine":
            prepare("wine", expected)
        expected_hashes = [item["sha256"] for item in check_data(expected, mode)]
        if [item["sha256"] for item in summary] != expected_hashes:
            raise RuntimeError(f"{version}: SHA-256 скачанных файлов отличается от генератора")
        graph = downloaded.get_dependency_graph()
        if graph.get(downloaded.id, []) != parents:
            raise RuntimeError(f"{version}: неверный lineage после скачивания")
        if mode == "iris_features" and ids["WINE_ID"] in graph:
            raise RuntimeError("Версия Wine обнаружена среди предков Iris features")
        changes = {"added": sorted(downloaded.list_added_files()),
                   "modified": sorted(downloaded.list_modified_files()),
                   "removed": sorted(downloaded.list_removed_files())}
        expected_changes = {"added": ["iris.csv"] if mode == "base" else (["wine.csv"] if mode == "wine" else []),
                            "modified": ["iris.csv"] if mode == "iris_features" else [], "removed": []}
        if changes != expected_changes:
            raise RuntimeError(f"{version}: неверные изменения файлов: {changes}")
        if sorted(downloaded.list_files()) != sorted(Path(item["path"]).name for item in summary):
            raise RuntimeError(f"{version}: список SDK отличается от скачанного состава")
        versions.append({"key": key, "id": downloaded.id, "version": downloaded.version,
                         "parents": parents, "graph": graph, "files": sorted(downloaded.list_files()),
                         "changes": changes, "tables": summary, "finalized": downloaded.is_final()})
        evidence_path.write_text(json.dumps({"project": PROJECT, "name": NAME, "ids": ids,
                                             "versions": versions}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Проверена версия {version}: {downloaded.id}")
    # Повторная проверка базы после создания обеих дочерних версий.
    if Dataset.get(dataset_id=ids["BASE_ID"]).list_files() != ["iris.csv"]:
        raise RuntimeError("Состав базы изменился")
    from build_report import build_report
    build_report(root)
    print("REPORT.md обновлён. Сохраните evidence/clearml.json и REPORT.md в Git.")


if __name__ == "__main__":
    main()
