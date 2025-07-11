import time

# Global debug flag
debug = False
_debug_status_printed = False

def set_debug(value):
    """Set the debug mode on or off and print status only when changed."""
    global debug, _debug_status_printed
    
    # Only take action if the debug value is actually changing
    if debug != value:
        debug = value
        _debug_status_printed = False # Reset the printed flag when status changes
    
    # Print status if it hasn't been printed since the last change
    if not _debug_status_printed:
        if debug:
            print("Debug mode enabled")
        else:
            print("Debug mode disabled")
        _debug_status_printed = True
    return debug

def get_debug():
    """Get the current debug state."""
    global debug
    return debug


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
    # Call the original print function
    original_print(*args, **kwargs)
    original_print()  # Print a new line after each call


# Set the custom print function
print = custom_print

def print_once(func):
    """Decorator to run a function only once."""
    called = False
    def wrapper(*args, **kwargs):
        nonlocal called
        if not called:
            called = True
            return func(*args, **kwargs)
    return wrapper

@print_on_change
def debug_print(*data, action=None, msg="Debug data"):
    """Print debug messages if debug mode is enabled."""
    global debug
    if action == None:
        action = ''
    else:
        action = f"[{action}]"
    if debug:
        print(f" {msg}: {action} - {data}\r \n")
