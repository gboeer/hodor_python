import pandas as pd
import pytest

from hodor_python.dataset import HodorDataError


class DummyDataset:
    def __init__(self, dataset_folder):
        self.dataset_folder = dataset_folder
        self.downloaded = {"video": [], "sonar": [], "sequence": []}

    @property
    def counts(self):
        return pd.DataFrame(
            {
                "SeqID": [1, 2],
                "DateTimeStart": ["2020-01-01", "2020-01-02"],
                "DateTimeEnd": ["2020-01-01", "2020-01-02"],
                "sequence_length": ["1:00:00", "1:00:00"],
                "fish_cod": [3, 0],
            }
        )

    def download_video(self, sequence_ids):
        self.downloaded["video"].extend(sequence_ids)

    def download_sonar(self, sequence_ids):
        self.downloaded["sonar"].extend(sequence_ids)

    def download_sequence(self, sequence_ids):
        self.downloaded["sequence"].extend(sequence_ids)


class DummyDatasetError(DummyDataset):
    @property
    def counts(self):
        raise HodorDataError("HODOR counts data failed to load.")

    def download_video(self, sequence_ids):
        raise HodorDataError("HODOR video download failed.")


def test_cli_list_default_columns(monkeypatch, capsys, tmp_path):
    from hodor_python import cli

    monkeypatch.setattr(cli, "HODOR_Dataset", DummyDataset)
    exit_code = cli.main(["--dataset-folder", str(tmp_path), "list", "--limit", "1"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "SeqID" in captured.out
    assert "1" in captured.out


def test_cli_list_unknown_column(monkeypatch, capsys, tmp_path):
    from hodor_python import cli

    monkeypatch.setattr(cli, "HODOR_Dataset", DummyDataset)
    exit_code = cli.main(
        [
            "--dataset-folder",
            str(tmp_path),
            "list",
            "--columns",
            "SeqID,missing_col",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Unknown columns" in captured.err


def test_cli_info_found(monkeypatch, capsys, tmp_path):
    from hodor_python import cli

    monkeypatch.setattr(cli, "HODOR_Dataset", DummyDataset)
    exit_code = cli.main(["--dataset-folder", str(tmp_path), "info", "1"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "SeqID" in captured.out
    assert "1" in captured.out


def test_cli_info_missing(monkeypatch, capsys, tmp_path):
    from hodor_python import cli

    monkeypatch.setattr(cli, "HODOR_Dataset", DummyDataset)
    exit_code = cli.main(["--dataset-folder", str(tmp_path), "info", "999"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "not found" in captured.err


def test_cli_counts_stdout(monkeypatch, capsys, tmp_path):
    from hodor_python import cli

    monkeypatch.setattr(cli, "HODOR_Dataset", DummyDataset)
    exit_code = cli.main(["--dataset-folder", str(tmp_path), "counts"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "SeqID" in captured.out


def test_cli_counts_file(monkeypatch, tmp_path):
    from hodor_python import cli

    monkeypatch.setattr(cli, "HODOR_Dataset", DummyDataset)
    output = tmp_path / "counts.csv"
    exit_code = cli.main(
        ["--dataset-folder", str(tmp_path), "counts", "--output", str(output)]
    )

    assert exit_code == 0
    assert output.exists()
    content = output.read_text()
    assert "SeqID" in content


def test_cli_download_modes(monkeypatch, tmp_path):
    from hodor_python import cli

    dataset = DummyDataset(tmp_path)

    def _factory(*_args, **_kwargs):
        return dataset

    monkeypatch.setattr(cli, "HODOR_Dataset", _factory)

    exit_code = cli.main(["--dataset-folder", str(tmp_path), "download", "1", "2"])
    assert exit_code == 0
    assert dataset.downloaded["sequence"] == [1, 2]

    exit_code = cli.main(
        ["--dataset-folder", str(tmp_path), "download", "3", "--video"]
    )
    assert exit_code == 0
    assert dataset.downloaded["video"] == [3]

    exit_code = cli.main(
        ["--dataset-folder", str(tmp_path), "download", "4", "--sonar"]
    )
    assert exit_code == 0
    assert dataset.downloaded["sonar"] == [4]


def test_cli_handles_counts_error(monkeypatch, capsys, tmp_path):
    from hodor_python import cli

    monkeypatch.setattr(cli, "HODOR_Dataset", DummyDatasetError)
    exit_code = cli.main(["--dataset-folder", str(tmp_path), "counts"])

    captured = capsys.readouterr()
    assert exit_code == 3
    assert "failed to load" in captured.err.lower()


def test_cli_handles_download_error(monkeypatch, capsys, tmp_path):
    from hodor_python import cli

    monkeypatch.setattr(cli, "HODOR_Dataset", DummyDatasetError)
    exit_code = cli.main(["--dataset-folder", str(tmp_path), "download", "1", "--video"])

    captured = capsys.readouterr()
    assert exit_code == 3
    assert "download failed" in captured.err.lower()
