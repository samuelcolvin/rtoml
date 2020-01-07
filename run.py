from utils import parse_datetime
import rtoml

success = rtoml.parse("""\
foo = 'bar'
bar.x = 1979-05-27T07:32:00Z
bar.y = ""
""", parse_datetime)
debug(success)

rtoml.parse('''

''', parse_datetime)
