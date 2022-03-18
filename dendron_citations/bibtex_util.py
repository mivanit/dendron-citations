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

# local imports
from dendron_citations.dc_util import (
	OptionalStr,OptionalListStr,OrderedDictType,
)

BIBTEX_ENTRY_TYPES_BASE : List[str] = [
	'article', 'book', 'booklet', 'conference', 'inbook', 'incollection', 
	'inproceedings', 'manual', 'masterthesis', 'misc', 'phdthesis', 'proceedings', 
	'techreport', 'unpublished', 'online', 'software',
]

BIBTEX_ENTRY_TYPES_LINESTART : List[str] = [
	'@' + typ + '{'
	for typ in BIBTEX_ENTRY_TYPES_BASE
]

def load_bibtex_raw(filename : str) -> OrderedDictType[str, biblib.bib.Entry]:
	"""load a bibtex file"""
	with open(filename, 'r', encoding = 'utf-8') as f:
		try:
			db : OrderedDictType[str, biblib.bib.Entry] = (
				biblib.bib
				.Parser()
				.parse(f, log_fp=sys.stderr)
				.get_entries()
			)
		except biblib.bib.FieldError as err:
			print('WARNING: ', err)
			raise

	# get the correct keys for the case
	all_keys : List[str] = list()
	with open(filename, 'r', encoding = 'utf-8') as f:
		for line in f:
			for typ  in BIBTEX_ENTRY_TYPES_LINESTART:
				if line.lower().startswith(typ):
					all_keys.append(line.split('{')[1].split(',')[0])

	# fix the keys in `db` with the matching correct-case keys in `all_keys`
	if not (len(all_keys) == len(db)): 
		raise ValueError(
			'manually read keys count doesnt match number of keys in database:\t'
			+ f'{len(all_keys) = }\t{len(db) = }'
		)

	db_new : OrderedDictType[str, biblib.bib.Entry] = OrderedDict()
	for key in all_keys:
		if key.lower() in db:
			db_new[key] = db[key.lower()]
		else:
			raise KeyError(f'key {key.lower()} not found in database, expected from `all_keys`')

	return db_new