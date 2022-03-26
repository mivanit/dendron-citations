"""citation entry class"""

# standard library imports
from typing import (
	Optional, Literal,
	Dict, List,
)


from collections import OrderedDict
from dataclasses import dataclass,asdict

# package imports
# implementation of mustache templating
import chevron # type: ignore 

import biblib.bib # type: ignore

# local imports
from dendron_citations.dc_util import (
	OptionalStr,OptionalListStr,OrderedDictType,
)
from dendron_citations.md_util import PandocMarkdown
from dendron_citations.process_meta import (
	safe_get,safe_get_any,safe_get_split,
	strip_bibtex_fmt,name_to_tag,
	process_tag_name,process_note_HACKY,
)
from dendron_citations.process_meta import Config



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
