# PV Watchdog

*This is a prototype. Do not use in production.*

Monitor changes in the state of a PV. Log all changes to stderr. If the rate of
change exceeds configurable (and optional) hourly, daily, or monthly limits,
log and (optionally) send an email to one or more addresses.

The emails are rate-limited to one per hour.

## Installation and Usage

Requires Python 3.7 or higher.

```
# Check that this is 3.7 or higher.
python -V

# Create and activate a separate software environment (recommended, not required)
python -m venv pv_watchdog_env
source pv_watchdog_env/bin/activate

# Install requirements.
python -m pip install -r requirements.txt

# See help for details.
./pv_watchdog --help

# Example:
./pv_watchdog --hourly 5 --emails engineer@example.com PV_NAME
```
