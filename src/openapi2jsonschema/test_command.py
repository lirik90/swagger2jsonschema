import filecmp
import os

import pytest  # type: ignore
from click.testing import CliRunner

from openapi2jsonschema.command import default

FIXTURE_DIR = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "..", "fixtures")
)


def test_help():
    runner = CliRunner()
    result = runner.invoke(default, ["--help"])
    assert result.exit_code == 0
    assert "Usage: default [OPTIONS] SCHEMA_URL" in result.output


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "oasv3", "petstore.yaml"),
    os.path.join(FIXTURE_DIR, "oasv3", "petstore.json"),
)
def test_command_oasv3(datafiles):
    runner = CliRunner()
    for spec in os.listdir(datafiles):
        output_dir = os.path.join(datafiles, "schemas")
        schema_url = os.path.join(datafiles, spec)
        result = runner.invoke(
            default,
            [
                "--output",
                output_dir,
                schema_url,
            ],
        )
        assert result.exit_code == 0
        assert filecmp.cmp(
            os.path.join(FIXTURE_DIR, "oasv3", "schemas", "all.json"),
            os.path.join(output_dir, "all.json"),
        )
        assert filecmp.cmp(
            os.path.join(FIXTURE_DIR, "oasv3", "schemas", "error.json"),
            os.path.join(output_dir, "error.json"),
        )
        assert filecmp.cmp(
            os.path.join(FIXTURE_DIR, "oasv3", "schemas", "pet.json"),
            os.path.join(output_dir, "pet.json"),
        )
        assert filecmp.cmp(
            os.path.join(FIXTURE_DIR, "oasv3", "schemas", "pets.json"),
            os.path.join(output_dir, "pets.json"),
        )


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "kubernetes", "swagger.json"),
)
def test_command_kubernetes(datafiles):
    runner = CliRunner()
    for spec in os.listdir(datafiles):
        output_dir = os.path.join(datafiles, "schemas")
        schema_url = os.path.join(datafiles, spec)
        result = runner.invoke(
            default,
            [
                "--output",
                output_dir,
                "--stand-alone",
                "--expanded",
                "--kubernetes",
                "--strict",
                schema_url,
            ],
        )
        assert result.exit_code == 0
        assert filecmp.cmp(
            os.path.join(FIXTURE_DIR, "kubernetes", "schemas", "_definitions.json"),
            os.path.join(output_dir, "_definitions.json"),
        )
        assert filecmp.cmp(
            os.path.join(FIXTURE_DIR, "kubernetes", "schemas", "all.json"),
            os.path.join(output_dir, "all.json"),
        )
        assert filecmp.cmp(
            os.path.join(FIXTURE_DIR, "kubernetes", "schemas", "pod-v1.json"),
            os.path.join(output_dir, "pod-v1.json"),
        )
