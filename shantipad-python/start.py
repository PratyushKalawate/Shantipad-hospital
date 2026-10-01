"""Set up and run the local hospital website with an interactive admin account."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import venv


ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".venv"
PYTHON = ENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def run(*args):
    subprocess.run([str(PYTHON), *args], cwd=ROOT, check=True)


if __name__ == "__main__":
    if not PYTHON.exists():
        venv.EnvBuilder(with_pip=True).create(ENV)
    dependencies_ready = subprocess.run(
        [str(PYTHON), "-c", "import django, PIL, whitenoise"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0
    if not dependencies_ready:
        run("-m", "pip", "install", "-r", "requirements.txt")
    run("manage.py", "migrate", "--noinput")
    run("manage.py", "seed_content")
    has_admin = subprocess.run([
        str(PYTHON), "manage.py", "shell", "-c",
        "from django.contrib.auth import get_user_model; import sys; sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 1)",
    ], cwd=ROOT, stdout=subprocess.DEVNULL).returncode == 0
    if not has_admin:
        print("\nCreate your admin login. Your password will not be shown while typing.\n")
        run("manage.py", "createsuperuser")
    print("\nWebsite: http://127.0.0.1:8000/")
    print("Admin:   http://127.0.0.1:8000/admin/\n")
    run("manage.py", "runserver", "127.0.0.1:8000")
