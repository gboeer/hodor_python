import importlib
import pytest

import dotenv
dotenv.load_dotenv(override=True)

def test_import_hodor_python():
    assert importlib.util.find_spec("hodor_python") is not None

def test_import_dataset():
    from hodor_python import dataset
    assert hasattr(dataset, "HODOR_Dataset")
    assert hasattr(dataset, "Species")

def test_hodor_dataset_init(tmp_path):
    from hodor_python import HODOR_Dataset
    ds = HODOR_Dataset(dataset_folder=tmp_path)
    assert hasattr(ds, "counts")
    assert callable(getattr(ds, "download_video", None))
    assert callable(getattr(ds, "download_sonar", None))
    assert callable(getattr(ds, "download_sequence", None))

def test_species_enum():
    from hodor_python import Species
    assert "FISH_COD" in Species.__members__
    assert Species.FISH_COD.value == "fish_cod"
