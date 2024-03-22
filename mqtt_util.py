import time

def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True


def wait_until(condition, timeout, period=0.1, *args, **kwargs):
  time_to_exit = time.time() + timeout
  while time.time() < time_to_exit:
    if condition():
        return True
    print(".", end="", flush=True)
    time.sleep(period)

  return False