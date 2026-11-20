'''Utility helper functions for the iot package.'''

def get_sensor_value(sensor: dict):
    """Return the appropriate reading value for a sensor based on its type.

    - ``temperature`` → ``sensor['temperature']``
    - ``humidity`` → ``sensor['humidity']``
    - fallback → ``sensor.get('value')``
    """
    sensor_type = sensor.get("type")
    if sensor_type == "temperature":
        return sensor.get("temperature")
    if sensor_type == "humidity":
        return sensor.get("humidity")
    if sensor_type == "sound":
        return sensor.get("sound")
    # Generic fallback
    return sensor.get("value")

