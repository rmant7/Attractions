#!/home/azureuser/ChipTripData/Python/scraping/Kiwi/.venv312/bin/python3.12
from functools import wraps
import json
from pathlib import Path
import time

import functions

from config import INPUTS_DIR, EXCLUDED_COUNTRIES, COUNTED_COUNTRIES, PORT_TYPES


# custom Exceptions to apart them from the exceptions raised in main()
class FuncException(Exception):
    pass


def limit_calls_per_minute(max_calls):
    """
    Decorator that limits a function to being called `max_calls` times per minute,
    with a delay between subsequent calls calculated based on the time since the
    previous call.
    """
    calls = []
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Remove any calls from the call history that are older than 1 minute
            calls[:] = [call for call in calls if call > time.time() - 60]
            if len(calls) >= max_calls:
                # Too many calls in the last minute, calculate delay before allowing additional calls
                time_since_previous_call = time.time() - calls[-1]
                delay_seconds = 60 / max_calls - time_since_previous_call
                if delay_seconds > 0:
                    time.sleep(delay_seconds)
            # Call the function and add the current time to the call history
            func(*args, **kwargs)
            calls.append(time.time())
            
        return wrapper
    return decorator


def rate_limited(limit=30, per=60):
    """
    A decorator that limits the number of calls to a function per period of time.
    Args:
        limit (int): The maximum number of calls allowed per period.
        per (int): The length of the period in seconds.
    Returns:
        function: The decorated function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if the function has a 'last_called' attribute
            if not hasattr(wrapper, 'last_called'):
                wrapper.last_called = 0

            # Calculate the time elapsed since the last call
            elapsed_time = time.time() - wrapper.last_called

            # If enough time has passed, reset the counter
            if elapsed_time > per:
                wrapper.call_count = 0

            # Check if the call count exceeds the limit
            if wrapper.call_count >= limit:
                # Calculate the remaining time in the current period
                remaining_time = per - elapsed_time

                # Sleep for the remaining time
                time.sleep(remaining_time)

                # Reset the call count after sleeping
                wrapper.call_count = 0

            # Call the actual function
            func(*args, **kwargs)

            # Update the last_called attribute and increment the call count
            wrapper.last_called = time.time()
            wrapper.call_count = getattr(wrapper, 'call_count', 0) + 1
        return wrapper
    return decorator


def elapsed_time(func):
    """
    A decorator that measures and prints the elapsed time for a function.
    Args:
        func (function): The function to be decorated.
    Returns:
        function: The decorated function.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        elapsed_minutes = int(elapsed // 60)
        elapsed_seconds = int(elapsed % 60)
        elapsed_hours = int(elapsed_minutes // 60)
        elapsed_minutes %= 60
        print(f'Elapsed time for {func.__name__}: {elapsed_hours} hours, '
                f'{elapsed_minutes} minutes, {elapsed_seconds} seconds')
    return wrapper


def load_json(path: str) -> dict:
    """
    This function loads a JSON file from a given path.
    The purpose of this function is to provide a convenient way to load JSON data from a file,
    while also handling potential errors that may occur during the loading process.
    Args:
        path (str): given path
    Returns:
        _type_: JSON data from a file
    """
    try:
        with open(Path(path), 'r') as f:
            return json.load(f)    
    except (FileNotFoundError, PermissionError, IsADirectoryError, TypeError) as e:
        print(f"Error loading JSON file '{path}': {str(e)}")
        raise Exception from e 
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file '{path}': {str(e)}")
        raise Exception from e    
    except Exception as e:
        print(f"An unexpected error occurred while loading JSON file '{path}': {str(e)}")
        raise Exception from e 


def limit_function_calls_per_api(max_calls, period_seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(api_key, *args, **kwargs):
            
            # Initialize per-function state only if it's not already set
            if not hasattr(wrapper, 'api_keys'):
                wrapper.api_keys = {}
            
            current_time = time.time()
            api_key_info = wrapper.api_keys.get(api_key, {'call_count': 0, 'last_reset_time': 0})

            if current_time - api_key_info['last_reset_time'] > period_seconds:
                # Reset the call count and last reset time if the period has elapsed
                api_key_info['call_count'] = 0
                api_key_info['last_reset_time'] = current_time

            if api_key_info['call_count'] < max_calls:
                api_key_info['call_count'] += 1
                api_key_info['last_reset_time'] = current_time
                wrapper.api_keys[api_key] = api_key_info
                return func(api_key, *args, **kwargs)
            else:
                if api_key in wrapper.api_keys.keys(): return None
                sleep_time = api_key_info['last_reset_time'] + period_seconds - current_time
                if sleep_time > 0:
                    print(f"Function {func.__name__} with API Key {api_key} has reached the maximum allowed calls in "
                        f"the specified period. Sleeping for {sleep_time:.2f} seconds.")
                    time.sleep(sleep_time)
                    # Recursively call the wrapper after sleeping
                    return wrapper(api_key, *args, **kwargs)
                else:
                    # If sleep_time is non-positive, reset the call count immediately
                    api_key_info['call_count'] = 1
                    api_key_info['last_reset_time'] = current_time
                    wrapper.api_keys[api_key] = api_key_info
                    return func(api_key, *args, **kwargs)

        # wrapper.api_keys = {}  # Dictionary to store API key information
        return wrapper
    return decorator


def get_cities(vehicle_type: str) -> list:
    cities = []
    for fp in Path(f'{INPUTS_DIR}/kiwi_cities_by_country').glob('*.json'):
        if fp.stem in EXCLUDED_COUNTRIES: continue
        data = functions.load_json(fp)
        cities += [city['id'] for city in data['locations'] if 
                   city['dst_popularity_score'] > 5000 and city[PORT_TYPES[vehicle_type]] > 0]
    return cities


if __name__ == '__main__':
    ...