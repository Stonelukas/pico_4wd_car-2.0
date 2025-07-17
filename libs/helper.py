import time

# Global debug flag
debug = False
_debug_status_printed = False
# Global storage for print_on_change function
_print_on_change_cache = {}

def print_on_change(message, key=None):
    """Print a message only when it has changed from the last call with the same key.
    
    Args:
        message: The message to print
        key: Optional key to track changes separately for different contexts
    """
    global _print_on_change_cache
    
    # Use the message itself as key if no key provided
    if key is None:
        key = id(message) if hasattr(message, '__hash__') else str(message)
    
    # Check if this message has changed
    if key not in _print_on_change_cache or _print_on_change_cache[key] != message:
        _print_on_change_cache[key] = message
        print(message)

# Global storage for print_once function
_print_once_cache = set()

def print_once(message, key=None):
    """Print a message only once per key.
    
    Args:
        message: The message to print
        key: Optional key to track separately for different contexts
    """
    global _print_once_cache
    
    # Use the message itself as key if no key provided
    if key is None:
        key = str(message)
    
    # Check if this key has been used before
    if key not in _print_once_cache:
        _print_once_cache.add(key)
        print(message)

def debug_print(message, key=None, action=None, msg="Debug data"):
    """Print debug messages only when they change, if debug mode is enabled.
    
    Args:
        message: The debug message/data to print
        key: Optional key to track changes separately for different contexts
        action: Optional action label
        msg: Debug message prefix
    """
    global debug
    if not debug:
        return
    
    # Create a unique key for this debug context
    debug_key = f"debug_{key}_{action}_{msg}" if key else f"debug_{action}_{msg}"
    
    # Format the debug message
    action_str = f"[{action}]" if action else ""
    formatted_message = f" {msg}: {action_str} - {message}\r \n"
    
    print_on_change(formatted_message, debug_key)

def clear_print_caches():
    """Clear all cached values for print_on_change and print_once functions."""
    global _print_on_change_cache, _print_once_cache
    _print_on_change_cache.clear()
    _print_once_cache.clear()
    
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


def print_on_change_decorator(func):
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

def print_once_decorator(func):
    """Decorator to run a function only once."""
    called = False
    def wrapper(*args, **kwargs):
        nonlocal called
        if not called:
            called = True
            return func(*args, **kwargs)
    return wrapper

@print_on_change_decorator
def debug_print_uses_decorator(*data, action=None, msg="Debug data"):
    """Print debug messages if debug mode is enabled."""
    global debug
    if action == None:
        action = ''
    else:
        action = f"[{action}]"
    if debug:
        print(f" {msg}: {action} - {data}\r \n")

class Timer:
    def __init__(self):
        self.start_time = 0

    def set_timer(self, offset: int):
        self.start_time: int = time.time_ns() + offset

    def expired(self):
        """Check if the timer has expired."""
        return True if time.time_ns() > self.start_time else False


