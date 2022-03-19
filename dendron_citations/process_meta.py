"""string processing, tag name conversion, safe getters for bibtex fields"""


# standard library imports
from typing import (
	Dict, List, Tuple, NamedTuple,
	Callable,
)

from collections import defaultdict
import unicodedata

# package imports
# import biblib # type: ignore

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
	OptionalStr,
)
from dendron_citations.config import Config



GLOBAL_AUTHORS_DICT : Dict[str,List[str]] = defaultdict(list)

BibLib_like_Name = NamedTuple('BibLib_like_Name', [
	('first',str),
	('last',str),
])


def strip_bibtex_fmt(s : str) -> str:
	return (
		unicodedata.normalize('NFKD', s)
		.encode('ascii', 'ignore').decode('ascii')
		.replace('{', '')
		.replace('}', '')
		.replace('\n', '  ')
		.replace('\r', '')
		.replace('\t', '  ')
		.strip()
		.rstrip(',')
		# .replace('\\', '')
	)

def process_tag_name(s : str, nodot : bool = True, kebab_case_tag_names : bool = False) -> str:
	s_new : str = (
		unicodedata.normalize('NFKD', s)
		.encode('ascii', 'ignore').decode('ascii')
		.replace(' - ', '-')
		.replace(' ', '_')
		.replace('\t', '__')
		.replace('\\', '')
		.replace('\n', '')
		.replace('/', '-')
	)

	if kebab_case_tag_names:
		s_new = s_new.replace('_', '-')
		s_new = s_new.lower()

	if nodot:
		s_new = s_new.replace('.', '-')
	
	return s_new

def to_alpha(s : str) -> str:
	"""convert a string to alphabetic only"""
	return ''.join(filter(str.isalpha, s))




def _name_to_tag_helper(name : str, kebab_case_tag_names : bool) -> str:
	return to_alpha(
		process_tag_name(name, kebab_case_tag_names = kebab_case_tag_names)
		.strip()
		.strip('_-,.}{')
	).lower()


# TODO: make this type work properly
Biblib_Name_Type = Tuple

def name_to_tag(name : Biblib_Name_Type, cfg : Config) -> str:
	"""convert a bibtex name to a tag name
	
	default format: `<first_char_of_first_name>-<last_name>`
	"""

	# if the first name is empty, we should check for the special case of 
	# 	the last name containing the full name in order
	if (name.first.strip() == '') and (name.last.strip().count(' ') > 0):
		temp : List[str] = name.last.strip('}{ \t').split(' ')
		if temp[0]:
			return name_to_tag(BibLib_like_Name(first = temp[0], last = temp[-1]), cfg)

	first : str = _name_to_tag_helper(name.first, kebab_case_tag_names = cfg.kebab_case_tag_names)
	last : str = _name_to_tag_helper(name.last, kebab_case_tag_names = cfg.kebab_case_tag_names)

	# make the first letters capital, checking for length
	if first:
		first = first[0].upper() + first[1:]
	if last:
		last = last[0].upper() + last[1:]

	# return
	output : str = ''

	if first == '':
		output = last

	elif last == '':
		output = first
	else:
		output = f'{first[0]}-{last}'

	# we write to this global dict to later be able to list all the author aliases in the tag file
	basic_str_name : str = f'{name.first} {name.last}'

	# global GLOBAL_AUTHORS_DICT
	if basic_str_name not in GLOBAL_AUTHORS_DICT[output]:
		GLOBAL_AUTHORS_DICT[output].append(basic_str_name)

	return 'author.' + output

def _handle_whitespace(s : str) -> str:
	output : List[str] = []
	for line in s.split('\n'):
		if line.strip():
			output.append(line)

	return '\n'.join(output)


def process_note_HACKY(s : OptionalStr) -> OptionalStr:
	"""a very very fragile attempt at making the bibtex notes look nice

	try to detect whether the note is html, latex, or plain markdown, and then use pandoc to convert it
	
	TODO: eventually this should just get the notes directly from zotero
	"""

	if s is None:
		return None

	# if we have pypandoc, try to process the notes as html or latex
	if PYPANDOC_AVAILABLE:
		if (s.count('<') / len(s) > 0.05) and (s.count('>') / len(s) > 0.05):
			# probably html
			try:
				return _handle_whitespace(
					pypandoc.convert_text(s, 'markdown', format = 'html')
					.replace('# ', '## ')
				)
			except RuntimeError as err:
				print(f"WARNING: couldn't convert note as HTML: {err}")

		elif s.count('\\') / len(s) > 0.01:
			# probably latex
			try:
				return _handle_whitespace(
					pypandoc.convert_text(s, 'markdown', format = 'latex')
					.replace('# ', '## ')
				)
			except RuntimeError as err:
				print(f"WARNING: couldn't convert note as LaTeX: {err}")

	# otherwise, assume plaintext/markdown and do some very fragile processing
	s = (
		s
		.replace('\\par', '\n\n') # replace \par with newlines
		.replace(r'{$>$}', '>') # undo escaping of `>`
		.replace(r'$>$', '>')
		.replace('\\#', '#') # undo escaping of `#`
		.replace('# ', '## ') # add heading level
		.replace("`", "\"") # quote escaping
		.replace("\'", "\"")
		.replace('\\', '') # get rid of all other backslashes
		.replace('\n ', '\n') # get rid of extra spaces at beginning of lines. not sure why these show up
	)

	# sometimes, not exports replace " " with "~". not a clue why.
	if s.count('~') / len(s) > 0.1:
		s = s.replace('~', ' ')

	return s


def safe_get(
		d : Dict, 
		key : str,
		default_factory : Callable = lambda : None,
		process : Callable = strip_bibtex_fmt,
	) -> str:
	
	if key in d:
		try:
			return process(d[key])
		except KeyError:
			return default_factory()
	else:
		return default_factory()

def safe_get_any(
		d : Dict, 
		keys : List[str],
		default_factory : Callable = lambda : None,
		process : Callable = strip_bibtex_fmt,
	) -> str:
	
	for key in keys:
		if key in d:
			try:
				return process(d[key])
			except KeyError:
				return default_factory()
	
	return default_factory()

def safe_get_split(
		d : Dict, 
		key : str, 
		sep : str, 
		default_factory : Callable = list,
		process : Callable = strip_bibtex_fmt,
	) -> List[str]:

	if key in d:
		try:
			return [
				process(x)
				for x in str(d[key]).split(sep)
			]
		except KeyError:
			return default_factory()
	else:
		return default_factory()
