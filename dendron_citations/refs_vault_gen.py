"""generate a vault of dendron notes from entries in a bibtex file

# Usage:

**gen** : generate reference notes:

	python refs_vault_gen.py gen [cfg_path] [kwargs]

**help** : print this help message and exit:

	python refs_vault_gen.py help

**print_cfg** : print to console an example config in either json or yaml:

	python refs_vault_gen.py print_cfg [--fmt=<format>]

# Generation:

when running
	python refs_vault_gen.py gen [cfg_path] [**kwargs]

`cfg_path` should be the location of a yaml or json config file
any of those items can be overwritten as keyword arguments using 
`--<keyword>=<value>`

the expected config elements, types, and default values are:
```python
	bib_filename : str = 'refs.bib'
	vault_loc : str = 'vault/'
	note_prefix : str = 'refs.'
	make_tag_notes : bool = True
	verbose : bool = False
	kebab_case_tag_names : bool = False
	template_path : Optional[str] = None
```

"""

# pylint: disable=invalid-name, bad-indentation

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
from dendron_citations.md_util import PandocMarkdown,gen_dendron_ID


# handle `OrderedDict` typing not working below 3.10
if (sys.version_info[1] < 10):
	# we declare the ordered dict as just a dict here
	# this will break MyPy, but it's fine
	OrderedDictType = Dict
else:
	OrderedDictType = OrderedDict


OptionalStr = Optional[str]
OptionalListStr = Optional[List[str]]


DEFAULT_TEMPLATE : str = """


{{#_bln_author_tags}}# Authors
{{/_bln_author_tags}}
{{#author_tags}}
 - [[{{str_name}} | tags.{{tag_name}}]]
{{/author_tags}}

{{#_bln_links}}# Links
{{/_bln_links}}
{{#links}}
 - [`{{elt}}`]({{elt}})
{{/links}}

{{#_bln_keywords}}# Keywords
{{/_bln_keywords}}
{{#keywords}}
 - #{{elt}}
{{/keywords}}

{{#_bln_files}}# Files
{{/_bln_files}}
{{#files}}
 - [`{{elt}}`]({{elt}})
{{/files}}

{{#abstract}}
# Abstract  
{{&abstract}}
{{/abstract}}

{{#note}}
# Notes
{{&note}}
{{/note}}
"""

def _get_template(self : 'Config') -> str:
	if self.template_path is not None:
		if os.path.isfile(self.template_path):
			try:
				with open(self.template_path, 'r', encoding = 'utf-8') as f:
					return str(f.read())
			except (OSError, IOError, FileNotFoundError) as err:
				print(f"WARNING: couldn't read template file {self.template_path}:\t{err}", file = sys.stderr)
				print("\twill use 'DEFAULT_TEMPLATE'")
				return DEFAULT_TEMPLATE
		else:
			print(f"WARNING: template file {self.template_path} not found", file = sys.stderr)
			print("\twill use 'DEFAULT_TEMPLATE'")
			return DEFAULT_TEMPLATE
	else:
		return DEFAULT_TEMPLATE

# TODO: how can we dynamically get the template and circumvent `frozen=True`?
# @dataclass(frozen=True)
@dataclass
class Config:
	"""config for generating reference notes"""
	bib_filename : str = 'refs.bib'
	vault_loc : str = 'vault/'
	note_prefix : str = 'refs.'
	make_tag_notes : bool = True
	verbose : bool = False
	kebab_case_tag_names : bool = False
	template_path : Optional[str] = None
	
	template : str = DEFAULT_TEMPLATE
	# template : str = cached_property(_get_template)

	def __post_init__(self):
		self.template = _get_template(self)


	def as_dict(self) -> Dict:
		return dict(
			bib_filename = self.bib_filename,
			vault_loc = self.vault_loc,
			note_prefix = self.note_prefix,
			make_tag_notes = self.make_tag_notes,
			verbose = self.verbose,
			kebab_case_tag_names = self.kebab_case_tag_names,
			template_path = self.template_path,
		)

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

GLOBAL_AUTHORS_DICT : Dict[str,List[str]] = defaultdict(list)


BibLib_like_Name = NamedTuple('BibLib_like_Name', [
	('first',str),
	('last',str),
])


def _name_to_tag_helper(name : str, kebab_case_tag_names : bool) -> str:
	return to_alpha(
		process_tag_name(name, kebab_case_tag_names = kebab_case_tag_names)
		.strip()
		.strip('_-,.}{')
	).lower()

def name_to_tag(name : 'biblib.Name', cfg : Config) -> str:
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



AuthorTagDictKeys = Literal['tag_name', 'str_name']
AuthorTagDict = Dict[AuthorTagDictKeys,str]

@dataclass(frozen = True)
class CitationEntry:
	"""a universal citation entry"""
	bib_key : OptionalStr = None
	zotero_key : OptionalStr = None
	title : OptionalStr = None
	authors : OptionalListStr = None
	author_tags : Optional[List[AuthorTagDict]] = None
	typ : OptionalStr = None
	date : OptionalStr = None
	links : OptionalListStr = None
	files : OptionalListStr = None
	keywords : OptionalListStr = None
	collections : OptionalListStr = None
	abstract : OptionalStr = None
	note : OptionalStr = None
	bib_meta : Optional[OrderedDictType[str, str]] = None

	@staticmethod
	def from_bib(bib_key, bib_entry : biblib.bib.Entry, cfg : Config) -> 'CitationEntry':
		"""create a citation entry from a biblib entry"""
		authors : List[str] = list()
		author_tags : Optional[List[AuthorTagDict]] = list()
		try:
			authors = [
				strip_bibtex_fmt(f'{nm.first} {nm.last}')
				for nm in bib_entry.authors()
			]

			author_tags = [
				{ 'tag_name' : name_to_tag(nm, cfg), 'str_name' : nm_str }
				for nm,nm_str in zip(bib_entry.authors(), authors)
			]

		except biblib.bib.FieldError as err:
			print('WARNING: ', err)

		return CitationEntry(
			bib_key = bib_key,
			title = safe_get(bib_entry, 'title'),
			authors = authors,
			author_tags = author_tags,
			typ = safe_get(bib_entry, 'typ'),
			date = safe_get(bib_entry, 'date'),
			links = safe_get_split(bib_entry, 'url', ';'),
			files = [
				x.replace(r'\:', ':').replace('\\\\', '/')
				for x in safe_get_split(bib_entry, 'file', ';')
			],
			keywords = [
				process_tag_name(x)	
				for x in safe_get_split(bib_entry, 'keywords', ',')
			],
			collections = safe_get_split(bib_entry, 'collections', ','),
			abstract = safe_get_any(bib_entry, ['abstract', 'abstractnote', 'abstractNote', 'summary']),
			note = process_note_HACKY(safe_get_any(
				bib_entry, 
				['note', 'notes', 'annote', 'annotation', 'annotations', 'comments'],
				process = lambda x : x,
			)),
			bib_meta = OrderedDict(bib_entry),
		)

	def serialize(self) -> Dict:
		"""serialize the object as a dict
		
		- lists into lists of dicts: 
			mustache only allows lists of dicts, not of literals
			so, each list of str is converted to a list of `{'elt' : val}`

		- booleans for list presence:
		    no way in moustache to check for presence of a list and render something just once
			so, for each iterable with key `name`, we add a key `_bln_name` with value `True`

		"""
		d_basic : Dict = asdict(self)
		d_out : Dict = dict()
		for k,v in d_basic.items():
			if isinstance(v, (list, tuple)):
				if all(isinstance(x, (str, float, int, bool)) for x in v):
					d_out[k] = [{'elt' : x} for x in v]
				else:
					d_out[k] = v
			else:
				d_out[k] = v

			if isinstance(v, (list, tuple, dict)):
				d_out['_bln_' + k] = bool(v)

		return d_out


	def to_md(self, template : str) -> PandocMarkdown:
		"""create a markdown string from a template"""
		note : PandocMarkdown = PandocMarkdown.get_dendron_template(
			fm = {"traitIds" : "referenceNote"},
		)

		note.yaml_data['title'] = self.title
		note.yaml_data['tags'] = self.keywords
		note.yaml_data['attached_files'] = self.files
		note.yaml_data['authors'] = self.authors
		note.yaml_data['bibtex_key'] = self.bib_key
		# note.yaml_data['__bibtex__'] = self.bib_meta
		# note.yaml_data['__entry__'] = self.serialize()

		note.content = chevron.render(template, self.serialize())

		return note

	def get_all_tags(self) -> List[str]:
		"""get all tags"""

		auth_tags_processed : List[str] = list()
		if self.author_tags:
			auth_tags_processed = [
				x['tag_name']
				for x in self.author_tags
			]
		
		return [
			*auth_tags_processed,
			*(self.keywords if self.keywords else list()),
			*(self.collections if self.collections else list()),
		]

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


def make_tag_note(tag : str, vault_loc : str) -> None:
	"""check for the existance of a tag note in the vault, and make it if it doesnt exist"""
	
	tag_path : str = f'{vault_loc}tags.{tag}.md'
	
	if os.path.exists(tag_path):
		return

	note : PandocMarkdown = PandocMarkdown.get_dendron_template(
		fm = dict(),
		do_id = True,
	)
	note.yaml_data['title'] = tag

	note.content = f'# {tag}\n\n'

	# global GLOBAL_AUTHORS_DICT
	# if its an author tag, figure out all the names for the author:
	if tag.startswith('author.'):
		# removeprefix only works in python 3.9+
		# authortag : str = tag.removeprefix('author.')
		authortag : str = tag[len('author.'):]

		note.content += '\n'.join([
			'## Author names:',
			'',
			'\n'.join([
				f'- {x}'
				for x in GLOBAL_AUTHORS_DICT[authortag]
			]),
		])

	with open(tag_path, 'w', encoding = 'utf-8') as f:
		f.write(note.dumps())

def full_process(cfg : Config):
	"""given a bibtex file, output a vault of dendron notes"""

	if cfg.verbose:
		print(cfg.as_dict())
	# load the bibtext as a bunch of biblib entries
	db : OrderedDictType[str, biblib.bib.Entry] = load_bibtex_raw(cfg.bib_filename)

	all_tags : List[str] = list()
	vault_prefix : str = cfg.vault_loc + cfg.note_prefix

	for key,val in db.items():
		if cfg.verbose:
			print(f'  processing key:\t{key}')

		# convert biblib entries to our format
		entry : CitationEntry = CitationEntry.from_bib(key, val, cfg = cfg)
		# save the tags for later
		all_tags.extend(entry.get_all_tags())

		# make the note
		note : PandocMarkdown = entry.to_md(cfg.template)
		fname : str = f'{vault_prefix}{key}.md'

		# handle note metadata
		if os.path.exists(fname):
			# if the filename exists, get the created time and id from the old note
			old_note : PandocMarkdown = PandocMarkdown()
			old_note.load(fname)

			if 'created' in old_note.yaml_data:
				note.yaml_data['created'] = old_note.yaml_data['created']

			if 'updated' in old_note.yaml_data:
				note.yaml_data['updated'] = old_note.yaml_data['updated']
			
			if 'id' in old_note.yaml_data:
				note.yaml_data['id'] = old_note.yaml_data['id']
			else:
				note.yaml_data['id'] = gen_dendron_ID()
		else:
			# we don't update the time unless the note is new
			note.update_time()
			note.yaml_data['id'] = gen_dendron_ID()

		# save the note
		with open(fname, 'w', encoding = 'utf-8') as f:
			f.write(note.dumps())
	
	# make notes for any given tag
	# dendron backlinks can be used to see which notes are linked to a tag
	# NOTE: existing notes will not be overwritten. 
	if cfg.make_tag_notes:
		for tag in set(all_tags):
			if cfg.verbose:
				print(f'  processing tag:\t{tag}')
			make_tag_note(tag, cfg.vault_loc)


def gen(cfg_path : Optional[str], **kwargs):
	"""read config from both file and kwargs, merge (kwargs overwrite), run `full_process`"""

	# change the working directory to the config file's directory
	# this is so that relative paths work
	file_data : Dict[str, Any] = dict()
	if cfg_path is not None:
		cfg_dir : str = os.path.dirname(cfg_path)
		os.chdir(cfg_dir)
		cfg_path_rel : str = os.path.relpath(cfg_path, cfg_dir)

		# load config from file
		if cfg_path is not None:
			with open(cfg_path_rel, 'r', encoding = 'utf-8') as f:
				if any(cfg_path_rel.endswith(x) for x in ['.yaml', '.yml']):
					file_data = yaml.load(f, Loader = yaml.FullLoader)
				elif cfg_path_rel.endswith('.json'):
					file_data = json.load(f)
				else:
					raise ValueError(f'unknown config file type: {cfg_path}')
	
	# merge configs and run
	cfg : Config = Config(**{**file_data, **kwargs})

	full_process(cfg)

def print_help():
	print(__doc__)
	sys.exit(0)

def print_cfg(fmt : str):
	"""prints the default config as either json or yaml"""
	cfg : Config = Config()
	if fmt.lower() == 'json':
		print(json.dumps(cfg.as_dict(), indent = 4))
	elif fmt.lower() in ['yml', 'yaml']:
		print(yaml.dump(cfg.as_dict(), default_flow_style = False))
	else:
		raise ValueError(f'unknown format: {fmt}')

def main(cfg_path : Optional[str] = None, **kwargs):
	if 'help' in kwargs or 'h' in kwargs:
		print_help()
	elif 'print_cfg' in kwargs:
		print_cfg(fmt = kwargs['fmt'] if 'fmt' in kwargs else 'json')
	else:
		gen(cfg_path, **kwargs)

# RUNME : Dict[str, Callable] = {
# 	'gen' : gen,
# 	'help' : print_help,
# 	'print_cfg' : print_cfg,
# }

if __name__ == '__main__':
	import fire # type: ignore
	fire.Fire(main)









