"""generates a vault of dendron notes corresponding to entries from a bibtex file


"""

from typing import *
import os
import sys
# import json
from collections import OrderedDict
from dataclasses import dataclass,asdict

import yaml
import chevron # implementation of mustache templating
import biblib.bib

from md_util import PandocMarkdown

OptionalStr = Optional[str]
OptionalListStr = Optional[List[str]]

def strip_bibtex_fmt(s : str) -> str:
	return (
		s
		.replace('{', '')
		.replace('}', '')
		.replace('\n', '  ')
		.replace('\r', '')
		.replace('\t', '  ')
		.strip()
		.rstrip(',')
		# .replace('\\', '')
	)

def safe_get(
		d : Dict, 
		key : str,
		default_factory : Callable = lambda : None,
		process : Callable = strip_bibtex_fmt,
	) -> str:
	
	if key in d:
		try:
			return str(d[key])
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
				return str(d[key])
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
			return list([
				process(x)
				for x in str(d[key]).split(sep)
			])
		except KeyError:
			return default_factory()
	else:
		return default_factory()


DEFAULT_TEMPLATE : str = """

# {{title}}

{{#_bln_authors}}# Authors
{{/_bln_authors}}
{{#authors}}
 - {{elt}}
{{/authors}}

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
{{abstract}}
{{/abstract}}
"""

@dataclass(frozen = True)
class CitationEntry:
	"""a universal citation entry"""
	bib_key : OptionalStr = None
	zotero_key : OptionalStr = None
	title : OptionalStr = None
	authors : OptionalListStr = None
	typ : OptionalStr = None
	date : OptionalStr = None
	links : OptionalListStr = None
	files : OptionalListStr = None
	keywords : OptionalListStr = None
	collections : OptionalListStr = None
	abstract : OptionalStr = None
	bib_meta : Optional[OrderedDict[str, str]] = None

	@staticmethod
	def from_bib(bib_key, bib_entry : biblib.bib.Entry) -> 'CitationEntry':
		"""create a citation entry from a biblib entry"""
		authors : List[str] = []
		try:
			authors = [
				strip_bibtex_fmt(f'{nm.first} {nm.last}')
				for nm in bib_entry.authors()
			]
		except biblib.bib.FieldError as e:
			print('WARNING: ', e)

		return CitationEntry(
			bib_key = bib_key,
			title = safe_get(bib_entry, 'title'),
			authors = authors,
			typ = safe_get(bib_entry, 'typ'),
			date = safe_get(bib_entry, 'date'),
			links = safe_get_split(bib_entry, 'url', ';'),
			files = safe_get_split(bib_entry, 'files', ';'),
			keywords = safe_get_split(bib_entry, 'keywords', ','),
			collections = safe_get_split(bib_entry, 'collections', ','),
			abstract = safe_get_any(bib_entry, ['abstract', 'abstractnote', 'abstractNote', 'summary']),
			bib_meta = dict(bib_entry),
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
				if all(isinstance(x, str) for x in v):
					d_out[k] = [{'elt' : x} for x in v]
			else:
				d_out[k] = v

			if isinstance(v, (list, tuple, dict)):
				d_out['_bln_' + k] = bool(v)

		return d_out


	def to_md(self, template : str = DEFAULT_TEMPLATE) -> PandocMarkdown:
		"""create a markdown string from a template"""
		note : PandocMarkdown = PandocMarkdown.get_dendron_template()

		note.yaml_data['title'] = self.title
		note.yaml_data['tags'] = self.keywords
		note.yaml_data['attached_files'] = self.files
		note.yaml_data['authors'] = self.authors
		note.yaml_data['bibtex_key'] = self.bib_key
		note.yaml_data['__bibtex__'] = self.bib_meta
		# note.yaml_data['__entry__'] = self.serialize()

		note.content = chevron.render(template, self.serialize())

		return note




def load_bibtex_raw(filename : str) -> OrderedDict[str, biblib.bib.Entry]:
	"""load a bibtex file"""
	with open(filename, 'r', encoding = 'utf-8') as f:
		try:
			db : OrderedDict[str, biblib.bib.Entry] = (
				biblib.bib
				.Parser()
				.parse(f, log_fp=sys.stderr)
				.get_entries()
			)
		except biblib.bib.FieldError as e:
			print('WARNING: ', e)
			raise

	return db


def full_process(bib_filename : str, vault_prefix : str = '../../refs-vault/ref.'):
	"""given a bibtex file, output a vault of dendron notes"""
	db : OrderedDict[str, biblib.bib.Entry] = load_bibtex_raw(bib_filename)

	for key,val in db.items():
		entry : CitationEntry = CitationEntry.from_bib(key, val)
		note : PandocMarkdown = entry.to_md()
		fname : str = f'{vault_prefix}{key}.md'

		# if the filename exists, get the created time and id from the old note
		if os.path.exists(fname):
			old_note : PandocMarkdown = PandocMarkdown()
			old_note.load(fname)

			if 'created' in old_note.yaml_data:
				note.yaml_data['created'] = old_note.yaml_data['created']
			
			if 'id' in old_note.yaml_data:
				note.yaml_data['id'] = old_note.yaml_data['id']

		note.update_time()

		with open(fname, 'w', encoding = 'utf-8') as f:
			f.write(note.dumps())

if __name__ == '__main__':
	import fire
	fire.Fire(full_process)









