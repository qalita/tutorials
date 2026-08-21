import os
import shlex
import io
from contextlib import redirect_stdout, redirect_stderr
from typing import Any, Dict, List, Optional, Sequence, Union

from airflow.sdk import BaseOperator, Context

# Use qalita as a Python package (tools-cli). We'll programmatically invoke the Click CLI.
from qalita.__main__ import cli as qalita_cli, add_commands_to_cli


class QalitaOperator(BaseOperator):
    """Run QALITA CLI commands within an Airflow task.

    Parameters
    ----------
    command : Union[str, Sequence[str]]
        CLI command arguments to pass to the QALITA CLI (excluding the binary).
        Accepts a string (parsed with shlex) or a sequence of strings.
    cli_bin : Optional[str]
        Path or name of the QALITA CLI binary. Defaults to env `QALITA_CLI_BIN` or `qalita`.
    env : Optional[Dict[str, str]]
        Extra environment variables to pass to the process (merged over os.environ).
    cwd : Optional[str]
        Working directory to run the process in.
    log_output : bool
        If True, stream stdout/stderr to task logs. Always captures output and returns stdout.
    """

    template_fields: Sequence[str] = ("command", "env")

    def __init__(
        self,
        command: Union[str, Sequence[str]],
        cli_bin: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        log_output: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.command = command
        self.cli_bin = cli_bin
        self.extra_env = env or {}
        self.cwd = cwd
        self.log_output = log_output

    def _build_args(self) -> List[str]:
        if isinstance(self.command, str):
            args = shlex.split(self.command)
        else:
            args = list(self.command)
        return args

    def _with_temp_cwd_and_env(self, func, env: Dict[str, str]) -> Any:
        previous_cwd = os.getcwd()
        previous_env: Dict[str, Optional[str]] = {}
        for key, value in env.items():
            previous_env[key] = os.environ.get(key)
        try:
            if self.cwd:
                os.chdir(self.cwd)
            os.environ.update(env)
            return func()
        finally:
            # restore env
            for key, prev in previous_env.items():
                if prev is None and key in os.environ:
                    del os.environ[key]
                elif prev is not None:
                    os.environ[key] = prev
            # restore cwd
            if self.cwd:
                os.chdir(previous_cwd)

    def execute(self, context: Context) -> str:
        # Merge extra env over current env; applied temporarily within the call
        env_overrides: Dict[str, str] = dict(self.extra_env)
        args = self._build_args()

        # Ensure CLI commands are registered
        add_commands_to_cli()

        self.log.info("Running QALITA (python package) with args: %s", " ".join(shlex.quote(p) for p in args))
        if self.cwd:
            self.log.info("Working directory: %s", self.cwd)

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        def _invoke_cli() -> int:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # Use Click's main entry with standalone_mode=False to avoid sys.exit
                return int(
                    qalita_cli.main(
                        args=args,
                        prog_name="qalita",
                        standalone_mode=False,
                    )
                    or 0
                )

        try:
            return_code = self._with_temp_cwd_and_env(_invoke_cli, env_overrides)
        except SystemExit as exc:
            # click can still raise SystemExit; capture code
            return_code = int(getattr(exc, "code", 1) or 0)
        except Exception as exc:
            # Unexpected error
            if self.log_output:
                err = stderr_buffer.getvalue()
                if err:
                    self.log.error(err.rstrip())
            raise RuntimeError(f"QALITA CLI raised an exception: {exc}")

        out = stdout_buffer.getvalue()
        err = stderr_buffer.getvalue()

        if self.log_output:
            if out:
                self.log.info(out.rstrip())
            if err:
                # click may send warnings/info to stderr
                self.log.warning(err.rstrip())

        if return_code != 0:
            raise RuntimeError(
                f"QALITA CLI exited with code {return_code}. Stderr: {err}"
            )

        return out
