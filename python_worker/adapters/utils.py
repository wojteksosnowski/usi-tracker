import re

class JsonPathExtractor:
    """
    Utility for extracting values from nested dictionaries/lists using dot-notation paths.
    Supports attribute filtering: path.to.list[attr=value].field
    Supports RP-style unwrapping: {"type": "obj", "value": ...}
    """

    @staticmethod
    def _unwrap_rp(val):
        if isinstance(val, dict) and "value" in val and "type" in val:
            return val["value"]
        return val

    @classmethod
    def get_value(cls, data, path, default=None):
        if not data or not path:
            return default

        parts = path.split('.')
        current = data

        for part in parts:
            # Handle array indexing or attribute filtering: name[attr=val] or name[0]
            array_match = re.match(r'^([^\[]+)\[([^\]]+)\]$', part)
            if array_match:
                key = array_match.group(1)
                condition = array_match.group(2)
                
                # Move to the list first (try current then try unwrapped)
                target_list = None
                if isinstance(current, dict) and key in current:
                    target_list = current[key]
                else:
                    unwrapped = cls._unwrap_rp(current)
                    if isinstance(unwrapped, dict) and key in unwrapped:
                        target_list = unwrapped[key]
                
                if target_list is None:
                    return default
                
                current = cls._unwrap_rp(target_list)
                if not isinstance(current, list):
                    return default

                # Handle [0], [1] etc.
                if condition.isdigit():
                    idx = int(condition)
                    if idx < len(current):
                        current = current[idx]
                    else:
                        return default
                # Handle [attr=val]
                elif '=' in condition:
                    attr_key, attr_val = condition.split('=', 1)
                    found = False
                    for item in current:
                        item_to_check = cls._unwrap_rp(item)
                        if isinstance(item_to_check, dict) and str(item_to_check.get(attr_key)) == attr_val:
                            current = item
                            found = True
                            break
                    if not found:
                        return default
                else:
                    return default
            else:
                # Normal dictionary access
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    unwrapped = cls._unwrap_rp(current)
                    if isinstance(unwrapped, dict) and part in unwrapped:
                        current = unwrapped[part]
                    else:
                        return default

        return cls._unwrap_rp(current) if current is not None else default
