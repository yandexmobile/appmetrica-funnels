#!/usr/bin/env python
'''
  run.py

  This file is a part of the AppMetrica.

  Copyright © 2017 YANDEX

  You may not use this file except in compliance with the License.
  You may obtain a copy of the License at https://yandex.com/legal/metrica_termsofuse/
'''

import os
import sys
import threading
import time

from app.run import main as app
from logs_api_int_script import main as updater

interupted = False
if 'LOGS_API_FETCH_INTERVAL' not in os.environ:
    LOGS_API_FETCH_INTERVAL = 12 * 60 * 60
else:
    LOGS_API_FETCH_INTERVAL = int(os.environ['LOGS_API_FETCH_INTERVAL'])


def update_loop():
    is_first = True
    print "Starting updater loop (interval = {} seconds)".format(LOGS_API_FETCH_INTERVAL)

    while not interupted:
        if is_first:
            print 'Loading historical data'
            updater(first_flag=True)
            print 'Finished loading historical data'
            is_first = False
        else:
            print "Run Logs API fetch"
            updater()
            sys.stdout.flush()
            if not interupted:
                time.sleep(LOGS_API_FETCH_INTERVAL)


def start_update_loop():
    thread = threading.Thread(target=update_loop)
    thread.daemon = True
    thread.start()
    return thread


def run_app():
    app()


def main():
    update_loop_thread = start_update_loop()
    run_app()
    interupted = True
    update_loop_thread.join()


if __name__ == '__main__':
    main()
