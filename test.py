import subprocess
import sys


def test_cli_help():
    "Test that the CLI starts up without errors."
    # This raises CalledProcessError if it exits with a nonzero exit code.
    subprocess.check_call(["python", "pv_watchdog.py", "-h"])


def test_basic_exercise():
    "Run a 'random walk' and check that the log output looks about right."
    test_ioc = subprocess.Popen(
        [sys.executable, "-m", "caproto.ioc_examples.random_walk"]
    )
    watchdog = subprocess.Popen(
        [sys.executable, "pv_watchdog.py", "--hourly", "1", "random_walk:x"],
        stderr=subprocess.PIPE,
    )
    try:
        # Collect log output for 10 seconds.
        watchdog.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        # Stop the watchdog process.
        watchdog.terminate()
        _, stderr = watchdog.communicate()
    assert "The hourly limit 1 was exceeded at 4 by random_walk:x" in stderr.decode()
    # Stop the test IOC.
    test_ioc.terminate()
    # Wait for everything to stop.
    test_ioc.wait()
    watchdog.wait()
