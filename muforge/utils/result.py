import typing

# we're creating a custom Result type that simulates Rust's Result<T, E>

class Result:
    def __init__(self, value = None, error = None):
        if (value is not None) and (error is not None):
            raise ValueError("Result cannot have both value and error")
        if (value is None) and (error is None):
            raise ValueError("Result must have either value or error")
        self._value = value
        self._error = error

    def is_ok(self) -> bool:
        return self._error is None

    def is_err(self) -> bool:
        return self._value is None

    def unwrap(self):
        if self.is_err():
            raise Exception(f"Called unwrap on an Err value: {self._error}")
        return self._value

    def unwrap_err(self):
        if self.is_ok():
            raise Exception(f"Called unwrap_err on an Ok value: {self._value}")
        return self._error
    
    def __bool__(self):
        return self.is_ok()
    
    @classmethod
    def Ok(cls, value=""):
        return cls(value=value)
    
    @classmethod
    def Err(cls, error=""):
        return cls(error=error)