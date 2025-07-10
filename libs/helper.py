import time

# Profiling
def profiler(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func


def print_on_change(func):
    '''Decorator to run a function only when the arguments change.'''
    last_args = None
    last_kwargs = None
    def wrapper(*args, **kwargs):
        nonlocal last_args, last_kwargs
        if args != last_args or kwargs != last_kwargs:
            last_args = args
            last_kwargs = kwargs.copy() if kwargs else None
            return func(*args, **kwargs)
    return wrapper

# Custom Print
original_print = print
# @print_on_change
def custom_print(*args, **kwargs):
    """Custom print function to also redirect output to a log file and print a new line after each call."""
    # with open(LOG_FILE, "a") as log_f:
    #     log_f.write(' '.join(map(str, args)) + '\n')
    original_print(*args, **kwargs)
    original_print()  # Print a new line after each call


# Set the custom print function
print = custom_print

def print_once(func):
    has_run = False
    """Decorator to print a message only once."""
    def wrapper(*args, **kwargs):
        nonlocal has_run
        if not has_run:
            func(*args, **kwargs)
            has_run = True
    return wrapper
