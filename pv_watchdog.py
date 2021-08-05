#!/usr/bin/env python
import argparse
import collections
from datetime import datetime, timedelta
import logging
from logging.handlers import SMTPHandler, QueueHandler, QueueListener
import queue
import socket
import time

from caproto.threading.client import Context
from ratelimitingfilter import RateLimitingFilter


logger = logging.getLogger("validator")


def main():
    parser = argparse.ArgumentParser(
        description="Watch for a PV to flip more than N times"
    )
    parser.add_argument("pv", type=str, help="PV name")
    parser.add_argument(
        "--emails",
        nargs="*",
        help="space-separated list of email addresses",
    )
    parser.add_argument(
        "--hourly",
        type=int,
        help="Hourly limit",
    )
    parser.add_argument(
        "--daily",
        type=int,
        help="Daily limit",
    )
    parser.add_argument(
        "--monthly",
        type=int,
        help="Montly limit",
    )
    args = parser.parse_args()

    log_handler = logging.StreamHandler()  # stderr
    log_handler.setLevel("INFO")
    logger.setLevel("INFO")
    logger.addHandler(log_handler)

    if args.emails:
        server_name = socket.gethostname()
        smtp_handler = SMTPHandler(
            mailhost="localhost",
            fromaddr=f"PV Watchdog <noreply@{server_name}>",
            toaddrs=args.emails,
            subject=(f"PV Watchdog threshold teached on " f"{server_name}"),
        )
        rate_limit = RateLimitingFilter(rate=1, per=3600, burst=1)
        smtp_handler.addFilter(rate_limit)
        smtp_handler.setLevel("WARNING")
        # Use QueueHandler in case sending email is slow. LogRecords flow
        # from QueueHandler -> Queue -> QueueListener -> SMTPHandler.
        cleanup_listener = True
        que = queue.Queue()
        queue_handler = QueueHandler(que)
        queue_listener = QueueListener(que, smtp_handler, respect_handler_level=True)
        logger.addHandler(queue_handler)
        queue_listener.start()
    else:
        cleanup_listener = False

    # Put an upper limit on how much history we keep to put a cap on memory
    # usage.
    history = collections.deque(maxlen=10_000)

    ONE_MONTH = timedelta(days=30)
    ONE_DAY = timedelta(days=1)
    ONE_HOUR = timedelta(hours=1)
    RATES = ["monthly", "hourly", "daily"]

    def process_update(sub, response):
        counters = dict.fromkeys(RATES, 0)
        history.append(response)
        now = datetime.fromtimestamp(response.metadata.timestamp)
        # Purge everything older than 30 days.
        for item in history:
            dt = now - datetime.fromtimestamp(item.metadata.timestamp)
            if dt > ONE_MONTH:
                history.popleft()
                continue
            counters["monthly"] += 1
            if dt > ONE_DAY:
                continue
            counters["daily"] += 1
            if dt > ONE_HOUR:
                continue
            counters["hourly"] += 1
        logger.info("PV watchdog processed %r", response)
        for rate in RATES:
            limit = getattr(args, rate)
            if (limit is not None) and (counters[rate] > limit):
                logger.warning(
                    f"The {rate} limit {limit} was exceeded at {counters[rate]} by {args.pv}"
                )

    context = Context()
    (pv,) = context.get_pvs(args.pv)
    sub = pv.subscribe(data_type="time")
    sub.add_callback(process_update)

    try:
        # Block forever while subscription spins on its threads.
        while True:
            time.sleep(1000)
    finally:
        if cleanup_listener:
            queue_listener.stop()


if __name__ == "__main__":
    main()
