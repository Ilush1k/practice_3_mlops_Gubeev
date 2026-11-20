"""Проверки неверных данных и структуры фактически записанных MLflow runs."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import mlflow
from mlflow import MlflowClient

from run_experiments import METRICS, ROOT, load_wine


class TestDatasetIntegrity(unittest.TestCase):
    def test_wrong_hash_is_rejected_before_reading_csv(self):
        with tempfile.TemporaryDirectory() as temporary:
            Path(temporary, "wine.csv").write_bytes(b"changed data")
            with patch("run_experiments.Dataset.get") as get_dataset, patch("run_experiments.pd.read_csv") as read_csv:
                get_dataset.return_value.is_final.return_value = True
                get_dataset.return_value.get_local_copy.return_value = temporary
                with self.assertRaisesRegex(ValueError, "SHA-256 Wine не совпадает"):
                    load_wine("test-dataset", "0" * 64)
                read_csv.assert_not_called()


class TestLoggedRuns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "verification.json"
        if not path.exists():
            raise unittest.SkipTest("Сначала выполните run_experiments.py")
        cls.result = json.loads(path.read_text(encoding="utf-8"))
        mlflow.set_tracking_uri(cls.result["tracking_uri"])
        cls.client = MlflowClient()
        cls.runs = [cls.client.get_run(run_id) for run_id in cls.result["run_ids"]]

    def test_six_completed_runs_with_different_configurations(self):
        self.assertEqual(len(self.runs), 6)
        self.assertEqual(len({run.info.run_id for run in self.runs}), 6)
        logreg, forest = [], []
        for run in self.runs:
            self.assertEqual(run.info.status, "FINISHED")
            if run.data.tags["model_family"] == "logistic_regression":
                logreg.append(run.data.params["C"])
            elif run.data.tags["model_family"] == "random_forest":
                forest.append((run.data.params["n_estimators"], run.data.params["max_depth"]))
        self.assertEqual(len(set(logreg)), 3)
        self.assertEqual(len(set(forest)), 3)

    def test_required_fields_and_identical_data_provenance(self):
        for run in self.runs:
            with self.subTest(run_id=run.info.run_id):
                self.assertTrue(set(METRICS + ("training_seconds",)) <= run.data.metrics.keys())
                self.assertEqual(run.data.params["random_state"], "42")
                for key in ["dataset_id", "dataset_sha256", "split_sha256", "session_id"]:
                    self.assertEqual(run.data.tags[key], self.result[key])
        split = self.result["split"]["indices"]
        parts = [set(split[name]) for name in ["train", "validation", "test"]]
        self.assertEqual(len(set.union(*parts)), 178)
        self.assertFalse(parts[0] & parts[1] or parts[0] & parts[2] or parts[1] & parts[2])

    def test_test_metrics_only_in_best_run(self):
        for run in self.runs:
            names = {name for name in run.data.metrics if name.startswith("test_")}
            expected = {"test_" + name for name in METRICS} if run.info.run_id == self.result["best_run_id"] else set()
            self.assertEqual(names, expected)
        self.assertEqual(self.result["test_metric_evaluations"], 1)
        self.assertTrue(self.result["predictions_match"])

    def test_current_batch_does_not_include_previous_runs(self):
        found = mlflow.search_runs(experiment_ids=[self.result["experiment_id"]],
                                  filter_string=f"tags.session_id = '{self.result['session_id']}'")
        self.assertEqual(set(found["run_id"]), set(self.result["run_ids"]))


if __name__ == "__main__":
    unittest.main()
