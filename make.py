from argparse import ArgumentParser
from glob import glob
from os import path
from platform import system

BLOCK_SEP = "=" * 40
SOURCES = glob("dendron_citations/*.py")
PYLINT_OPTIONS =
"--disable=invalid-name,bad-indentation,use-list-literal,use-dict-literal,"
FLAG_PTHREAD = "-lpthread" if system() == "Windows" else "-pthread"

VENV_NAME = "env"
PIP_BIN = path.join(VENV_NAME, "Scripts", "pip")

def shell(cmd: str, *args, **kwargs):
    kwargs["shell"] = True
    return run(cmd, *args, **kwargs)

def print_with_block_sep(string):
    print(f"{BLOCK_SEP}\n{string}\n{BLOCK_SEP}")

def namespace(cls):
    """Make every method of cls a static method"""
    for name, nameval in cls.__dict__.items():
        if callable(nameval):
            cls.__dict[name] = staticmethod(nameval)
    return cls

@namespace
class Commands:
    def setup_env():
        """"set up a virtual environment, install dependencies, and
install the package"""
        print_with_block_sep("# setting up virtual environment")
        shell("python -m venv env", shell=True)

        print_with_block_sep("# installing package dependencies")
        shell(f"{PIP_BIN} install -r requirements.txt", shell=True)

        print_with_block_sep("# installing dev dependencies")
        shell(f"{PIP_BIN} install -r requirements_dev.txt", shell=True)

        print_with_block_sep("# installing package")
        shell(f"{PIP_BIN} install -e .")

        print_with_block_sep("# installation complete!")

    def env_clean():
        """clean up any existing virtual environemnts"""
        run(f"rm -rf {VENV_NAME}")

    def check():
        """run mypy, pylint"""

        print(f"Will run on files: {SOURCES}")

        print_with_block_sep("# running mypy")
        mypy_bin = path.join(VENV_NAME, "Scripts", "mypy")
        shell(f"{mypy_bin} {SOURCES}")

        print_with_block_sep("# running pylint")
        pylint_bin = path.join(VENV_NAME, "Scripts", "pylint")
        shell(f"{pylint_bin} {SOURCES} {PYLINT_OPTIONS}")

        print_with_block_sep("# type checking complete!")

def main():
    """Docstring"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    for cmd, cmd_func in Command.__dict__.items():
        subparsers.add_parser(cmd,
help=cmd_func.__doc__).set_defaults(func=cmd_func)

    parser.parse_args().func()

if __name__ == "__main__":
    main()
else:
    assert False # really don't want this file to be used as a library
