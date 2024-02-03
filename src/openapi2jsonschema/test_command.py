import os
import pytest  # type: ignore
import filecmp
from click.testing import CliRunner

from openapi2jsonschema.command import default

FIXTURE_DIR = f"{os.path.dirname(os.path.realpath(__file__))}/../fixtures"


def test_help():
    runner = CliRunner()
    result = runner.invoke(default, ["--help"])
    assert result.exit_code == 0
    assert "Usage: default [OPTIONS] SCHEMA_URL" in result.output


@pytest.mark.datafiles(
    f"{FIXTURE_DIR}/oasv3/petstore.yaml",
)
def test_command_oasv3(datafiles):
    runner = CliRunner()
    for spec in os.listdir(datafiles):
        output_dir = f"{datafiles}/schemas"
        schema_url = f"{datafiles}/{spec}"
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
            f"{FIXTURE_DIR}/oasv3/schemas/all.json",
            f"{output_dir}/all.json",
        )
        assert filecmp.cmp(
            f"{FIXTURE_DIR}/oasv3/schemas/error.json",
            f"{output_dir}/error.json",
        )
        assert filecmp.cmp(
            f"{FIXTURE_DIR}/oasv3/schemas/pet.json",
            f"{output_dir}/pet.json",
        )
        assert filecmp.cmp(
            f"{FIXTURE_DIR}/oasv3/schemas/pets.json",
            f"{output_dir}/pets.json",
        )


@pytest.mark.datafiles(
    f"{FIXTURE_DIR}/kubernetes/swagger.json",
)
def test_command_kubernetes(datafiles):
    runner = CliRunner()
    for spec in os.listdir(datafiles):
        output_dir = f"{datafiles}/schemas"
        schema_url = f"{datafiles}/{spec}"
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
            f"{FIXTURE_DIR}/kubernetes/schemas/_definitions.json",
            f"{output_dir}/_definitions.json",
        )
        assert filecmp.cmp(
            f"{FIXTURE_DIR}/kubernetes/schemas/all.json",
            f"{output_dir}/all.json",
        )
