import time

import pytimeparse


def verify(verify_function, timeout, *args, **kwargs):
    time_start = time.time()

    while time.time() - time_start < timeout:
        if verify_function(*args, **kwargs):
            return True
        time.sleep(1)

    return False


def parse_literal_time(source_time):
    return pytimeparse.parse(source_time)
