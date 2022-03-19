"""miscellaneous utilities for dendron_citations"""

# standard library imports
from typing import (
	Optional, Dict, List,
)

import sys
from collections import OrderedDict

# handle `OrderedDict` typing not working below 3.10
if (sys.version_info[1] < 10):
	# we declare the ordered dict as just a dict here
	# this will break MyPy, but it's fine
	OrderedDictType = Dict
else:
	OrderedDictType = OrderedDict


OptionalStr = Optional[str]
OptionalListStr = Optional[List[str]]
