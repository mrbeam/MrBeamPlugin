from functools import wraps

from octoprint_mrbeam.model import EmptyImport


def prevent_execution_on_import_error(import_to_check, default_return=None, callable=None, params=None):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if is_empty_import(import_to_check):
                if callable is None:
                    return default_return
                elif params is None:
                    return callable()
                else:
                    return callable(*params)

            result = function(*args, **kwargs)
            return result

        return wrapper

    return decorator


def is_empty_import(import_to_check):
    return isinstance(import_to_check, EmptyImport)
