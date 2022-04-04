import subprocess
import functools
import shutil


def run_and_capture(*args):
    result = subprocess.run(
        list(args),
        capture_output=True,
        text=True,
    )
    try:
        result.check_returncode()
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise
    else:
        return result.stdout


def run_without_capture(*args):
    return subprocess.run(
        list(args),
        check=True,
    )


class ExternalCommands:
    def __init__(self, commands, capture_output=True, check_available=True):
        self._commands = commands
        for cmd in self._commands:
            if capture_output:
                setattr(self, cmd, functools.partial(run_and_capture, cmd))
            else:
                setattr(self, cmd, functools.partial(run_without_capture, cmd))
        if check_available:
            self._check_available()

    def _check_available(self):
        for cmd in self._commands:
            if shutil.which(cmd) is None:
                raise RuntimeError(
                    f'Executable not found: {cmd}.'
                    + ' Make sure all dependencies are installed.'
                )
