from datetime import datetime

from utils import parse_datetime
import rtoml

success = rtoml.deserialize("""\
foo = 'bar'
bar.x = 1979-05-27T07:32:00Z
bar.y = ""
""", parse_datetime)
debug(success)

rtoml.deserialize('''

''', parse_datetime)
print(rtoml.serialize({
    'x': 1,
    'list': [1, 2, 3],
    'tuple': (3, 4, 5),
    # 'set': {3, 4, 5},
    'none': None,
    'dt': datetime.now(),
    'sub_dict': {
        'x': 2,
        'y': '345',
        'another': {
            'x': 1,
            'y': 2,
        }
    },
    'big_list': [
        {'a': 'x' * 10},
        {'a': 'y' * 10},
        {'a': 'z' * 10},
    ],
}))
