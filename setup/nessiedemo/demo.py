# -*- coding: utf-8 -*-
"""NessieDemo TODO docs."""
import os
import stat
import subprocess  # noqa: S404
import sys
from typing import TypeVar

import requests
import yaml


T = TypeVar("T", bound="NessieDemo")


class NessieDemo:
    """NessieDemo TODO docs."""

    nessie_process_wait_seconds: float = 2.0

    versions_yaml: str = None
    demos_root: str = "https://raw.githubusercontent.com/snazy/nessie-demos/master"

    nessie_api_uri: str = "http://localhost:19120/api/v1"

    native_runner_root: str = "https://github.com/projectnessie/nessie/releases/download"

    _versions_dict: dict = None

    _nessie_native_runner: os.path = None
    _nessie_process: subprocess.Popen = None

    _assets_dir: os.path = None

    def __init__(self: T, versions_yaml: str, demos_root: str = None) -> None:
        """Nessie demo TODO docs."""
        self.versions_yaml = versions_yaml
        if demos_root:
            self.demos_root = demos_root

        versions_url = "{}/configs/{}".format(self.demos_root, self.versions_yaml)

        self._assets_dir = os.path.join(os.getcwd(), "_assets")

        self._versions_dict = yaml.safe_load(_Util.curl(versions_url))

    def __str__(self: T) -> str:
        """Todo the docs."""
        return "Nessie-Demo: Nessie {nessie_version} ({nessie_running}), Apache Iceberg {iceberg_version}".format(
            nessie_version=self.get_nessie_version(),
            iceberg_version=self.get_iceberg_version(),
            nessie_running="RUNNING" if self.is_nessie_running() else "not running",
        )

    def get_nessie_version(self: T) -> str:
        """Todo the docs."""
        return self._versions_dict["versions"]["nessie"]

    def get_pynessie_version(self: T) -> str:
        """Todo the docs."""
        return self._versions_dict["versions"]["pynessie"]

    def get_iceberg_version(self: T) -> str:
        """Todo the docs."""
        return self._versions_dict["versions"]["iceberg"]

    def _prepare(self: T) -> None:
        # Install Python dependencies
        if "python_dependencies" in self._versions_dict:
            deps = self._versions_dict["python_dependencies"]
            _Util.exec_fail([sys.executable, "-m", "pip", "install"] + ["{}=={}".format(k, v) for k, v in deps.items()])

        # Download nessie native runner binary
        self._nessie_native_runner = os.path.join(
            self._assets_dir,
            "nessie-quarkus-{}-runner".format(self.get_nessie_version()),
        )

        if os.path.exists(self._nessie_native_runner) and os.stat(self._nessie_native_runner).st_mode & stat.S_IXUSR == stat.S_IXUSR:
            return

        nessie_native_runner_url = None
        try:
            nessie_native_runner_url = self._versions_dict["uris"]["nessie_native_image_binary"]
        except KeyError:
            pass
        if not nessie_native_runner_url:
            nessie_native_runner_url = "{}/nessie-{}/nessie-quarkus-{}-runner".format(
                self.native_runner_root,
                self.get_nessie_version(),
                self.get_nessie_version(),
            )

        # TODO find a way to either download binaries to the same place (don't download AND STORE the same binary again)
        # TODO find a way to remove the downloaded binaries

        _Util.wget(nessie_native_runner_url, self._nessie_native_runner)

    def is_nessie_running(self: T) -> bool:
        """Nessie docs TODO."""
        if self._nessie_process and not self._nessie_process.poll():
            return True
        return False

    def start(self: T) -> None:
        """Nessie demo TODO docs."""
        self._prepare()

        if self._nessie_process:
            exit_code = self._nessie_process.poll()
            if not exit_code:
                # Nessie process is still alive, leave it running.
                return

        # TODO need a way to actually _prevent_ multiple Nessie server instances
        #  (in case steps are repeated, notebooks reloaded, etc)

        # TODO capture stdout+stderr using a daemon thread and pipe it to the notebook
        std_capt = open("nessie-runner-output.log", "wb")
        try:
            print("Starting Nessie...")

            self._nessie_process = subprocess.Popen(self._nessie_native_runner, stderr=std_capt, stdout=std_capt)  # noqa: S603

            try:
                std_capt.close()
                self._nessie_process.wait(self.nessie_process_wait_seconds)
                with open("nessie-runner-output.log") as log:
                    log_lines = log.readlines()
                raise Exception(
                    "Nessie process disappeared. Exit-code: {}, stdout/stderr:\n  {}".format(
                        self._nessie_process.returncode, "  ".join(log_lines)
                    )
                )
            except subprocess.TimeoutExpired:
                print("Nessie running with PID {}".format(self._nessie_process.pid))
                pass
        except Exception:
            std_capt.close()
            os.unlink("nessie-runner-output.log")
            raise

    def stop(self: T) -> None:
        """Nessie demo TODO docs."""
        if self._nessie_process:
            print("Stopping Nessie ...")
            exit_code = self._nessie_process.poll()
            if not exit_code:
                self._nessie_process.terminate()
                self._nessie_process.wait()
            print("Nessie stopped")

    def fetch_dataset(self: T, dataset_name: str) -> dict[str, os.path]:
        """Nessie demo TODO docs."""
        dataset_root = "{}/datasets/{}/".format(self.demos_root, dataset_name)
        contents = _Util.curl("{}/ls.txt".format(dataset_root)).decode("utf-8").split("\n")
        dataset_dir = os.path.join(self._assets_dir, "datasets/{}".format(dataset_name))
        if not os.path.isdir(dataset_dir):
            os.makedirs(dataset_dir)
        name_to_path = dict()
        for file_name in contents:
            file_name = file_name.strip()
            if len(file_name) > 0 and not file_name.startswith("#"):
                url = "{}/{}".format(dataset_root, file_name)
                f = os.path.join(dataset_dir, file_name)
                if not os.path.exists(f):
                    _Util.wget(url, f)
                name_to_path[file_name] = f

        print("Dataset {} with files {}".format(dataset_name, ", ".join(name_to_path.keys())))

        return name_to_path


class _Util:
    @staticmethod
    def exec_fail(args: list[str]) -> None:
        print("Executing {} ...".format(" ".join(args)))
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: S603
        if result.returncode != 0:
            raise Exception("Executable failed. args: {}, stdout={}, stderr={}".format(" ".join(result.args), result.stdout, result.stderr))

    @staticmethod
    def wget(url: str, target: os.path, executable: bool = False) -> None:
        try:
            print("Downloading {} ...".format(url))
            with requests.get(url, stream=True) as resp:
                if not resp.ok:
                    raise Exception("Could not fetch {}, HTTP/{} {}".format(url, resp.status_code, resp.reason))
                with open(target, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=65536):
                        f.write(chunk)
                if executable:
                    os.chmod(
                        target,
                        os.stat(target).st_mode | stat.S_IXUSR,
                    )
            print("Completed download of {}".format(url))
        except Exception:
            if os.path.exists(target):
                os.unlink(target)
            raise

    @staticmethod
    def curl(url: str) -> bytes:
        with requests.get(url) as resp:
            if resp.ok:
                return resp.content
            else:
                raise Exception("Could not fetch {}, HTTP/{} {}".format(url, resp.status_code, resp.reason))
