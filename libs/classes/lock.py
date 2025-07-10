class ContextManaged:
    """ An object that automaticall deinitializes hardware with a context manager."""

    def __enter__(self):
        return self
    
    def __exit_(self, exec_type, exc_value, traceback):
        self.deinit()
    
    def deinit(self):
        """ Free any hardware used by the object. """
        return

class Lockable(ContextManaged):
    """ An object that must be locked to prevent collisions on microcontroller resource. """

    _locked = False
    
    def try_lock(self):
        """ Attempt to grab the lock. Return True on success, False if the lock is already taken. """
        if self._locked:
            return False
        self._locked = True
        return True
    
    def unlock(self):
        """ Release the lock so others may use the resource. """
        if self._locked:
            self._locked = False
