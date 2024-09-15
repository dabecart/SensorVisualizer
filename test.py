import re
from collections import defaultdict
from base64 import b64decode

def _parseDict(input: str) -> dict[str, any]:
        # Substitute all special characters.
        input = input.replace("\n", "\\n")\
                     .replace("\r", "\\r")\
                     .replace("\t", "\\t")\
                     .replace("\b", "\\b")\
                     .replace("\f", "\\f")

        # Regex: starts with {, ends with }
        dictRegex = r'\{([^{}]*)\}'
        dicts = re.findall(dictRegex, input)
        
        # Initialize a defaultdict to handle multiple values for the same key.
        resultDict = defaultdict(list)
        
        dictStr: str
        for dictStr in dicts:
            # Regex to match key-value pairs ->  name : value,
            keyValueRegex = r'(\w+)\s*:\s*(.+?)(?=,\s*\w+\s*:|$)'
            matches = re.findall(keyValueRegex, dictStr)

            key: str
            value: str
            for key, value in matches:
                # Convert value to the appropriate type.
                if value.isdigit():
                    value = int(value)
                else:
                    try:
                        value = float(value)
                    except ValueError:
                        # Remove the trailing '' and "".
                        if (value.startswith('b"') and value.endswith('"')) or \
                        (value.startswith("b'") and value.endswith("'")):
                            # Remove the head and tail.
                            value = value[2:-1]
                            value = b64decode(value)
                        else:
                            value = value.strip('\'"')
                            # Reconvert again the special characters.
                            value = value.replace("\\n", "\n")\
                                         .replace("\\r", "\r")\
                                         .replace("\\t", "\t")\
                                         .replace("\\b", "\b")\
                                         .replace("\\f", "\f")

                # Append value to the list of values for this key.
                resultDict[key].append(value)

        # Convert lists with a single item back to a single value.
        for key in resultDict:
            if len(resultDict[key]) == 1:
                resultDict[key] = resultDict[key][0]

        return dict(resultDict)

d = _parseDict('{name: Danotests, variable: 3108}')
print(d)