# PV Watchdog

*This is a prototype. Do not use in production.*

Monitor changes in the state of a PV. Log all changes to stderr. If the rate of
change exceeds configurable (and optional) hourly, daily, or monthly limits,
log and (optionally) send an email to one or more addresses.

The emails are rate-limited to one per hour.

```
./pv_watchdog --help
```

Example:

```
./pv_wtachdog --hourly 5 --emails engineer@example.com PV_NAME
```
