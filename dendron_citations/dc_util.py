"""miscellaneous utilities for dendron_citations"""

# standard library imports
from typing import (
	Optional, Literal, Any,
	Dict, List, NamedTuple,
	Callable,
)

import os
import sys
import json
from collections import OrderedDict, defaultdict
from dataclasses import dataclass,asdict
import unicodedata

# package imports
import yaml # type: ignore

# implementation of mustache templating
import chevron # type: ignore 

import biblib.bib # type: ignore

# optional pypandoc stuff
try:
	import pypandoc # type: ignore
	try:
		pypandoc.get_pandoc_version()
		PYPANDOC_AVAILABLE = True
	except RuntimeError as e:
		PYPANDOC_AVAILABLE = False
		print(f"WARNING: pypandoc couldn't find pandoc: {e}")

except ImportError:
	PYPANDOC_AVAILABLE = False
	print('WARNING: pypandoc not available. converting notes from bibtex might not work')

# handle `OrderedDict` typing not working below 3.10
if (sys.version_info[1] < 10):
	# we declare the ordered dict as just a dict here
	# this will break MyPy, but it's fine
	OrderedDictType = Dict
else:
	OrderedDictType = OrderedDict


OptionalStr = Optional[str]
OptionalListStr = Optional[List[str]]
