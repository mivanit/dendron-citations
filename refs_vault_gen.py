"""generating a vault of dendron notes corresponding to entries from a bibtex file (or in a zotero library)


# desired features:

## bibtex integration
given a bibtex file, generate a vault of dendron notes bibtex keys as filenames

- add tags and other things from bibtex to metadata
- "beneath" each note for the bibtex, add another note for the citation itself.
	- note that this will all break if the bibtex keys change!
- this allows the user to reference the dendron notes instead of raw bibtex item
	- lets us use backlink features from dendron to see where something is cited

## zotero integration

do everything as for bibtex integration, but also:

- add links/copies in zotero to the dendron notes (when they exist)
- have zotero item materials inside dendron file
	- zotero notes, plaintext attachments inline
	- links to all other attachments
	- exclude the dendron file to avoid recursion, haha

## other

- to allow simpler references to papers, without having to type `[[dendron://refs-vault/<bibtex key>]]`, the user may create a snippet:
```json
"dendron-cite": {
	"prefix": "@",
	"body": [
		"[[dendron://refs-vault/refs.$1]]"
	],
	"description": "dendron reference citation"
},
```


# dependencies:
- https://github.com/t-wissmann/biblib
	- note: forked from https://github.com/aclements/biblib, which no longer works

"""

from typing import *
import os
import sys
# import json
from collections import OrderedDict
from dataclasses import dataclass,asdict

import yaml
import biblib.bib

from md_util import PandocMarkdown

OptionalStr = Optional[str]
OptionalListStr = Optional[List[str]]

@dataclass(frozen = True)
class CitationEntry:
	"""a universal citation entry"""
	bib_key : OptionalStr = None
	zotero_key : OptionalStr = None
	title : OptionalStr = None
	authors : OptionalListStr = None
	typ : OptionalStr = None
	date : OptionalStr = None
	links : Optional[OrderedDict[str, str]] = None
	files : OptionalListStr = None
	keywords : OptionalListStr = None
	collections : OptionalListStr = None
	abstract : OptionalStr = None
	bib_meta : Optional[OrderedDict[str, str]] = None

	@staticmethod
	def from_bib(bib_key, bib_entry : biblib.bib.Entry) -> 'CitationEntry':
		"""create a citation entry from a biblib entry"""
		return CitationEntry(
			bib_key = bib_key,
			title = bib_entry.title,
			authors = bib_entry.authors,
			typ = bib_entry.typ,
			date = bib_entry.date,
			links = bib_entry.links,
			files = bib_entry.files,
			keywords = bib_entry.keywords,
			collections = bib_entry.collections,
			abstract = bib_entry.abstract,
			bib_meta = bib_entry.meta,
		)


def BibDatabase_serialize(db: Dict[str, biblib.bib.Entry]) -> Dict[str, Dict]:
	db_dict : Dict[str, Dict] = dict()

	for key, entry in db.items():
		
		temp_od : OrderedDict = OrderedDict(entry)
		temp_meta : dict = dict()

		temp_meta['typ'] = entry.typ
		temp_meta['key'] = key

		temp_meta['authors_lst'] = list()
		try:
			temp_authors_lst : List[str] = [
				f'{nm.last}, {nm.first}'
				for nm in entry.authors()
			]
		except biblib.bib.FieldError as e:
			print('WARNING: ', e)
			temp_meta['authors_lst'] = list()

		temp_meta['keywords_lst'] = entry['keywords'].split(',') if 'keywords' in entry else []
		temp_meta['files_lst'] = entry['files'].split(';') if 'files' in entry else []
		temp_meta['title_txt'] = entry['title'].replace('{', '').replace('}', '').replace('\n', ' ').replace('\r', '')

		db_dict[key] = dict({
			**temp_od,
			**temp_meta,
		})


	return db_dict


def load_bibtex(filename : str) -> OrderedDict[str, OrderedDict]:
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

	return BibDatabase_serialize(db)






def single_bib_to_dendron(entry : Dict[str, Union[str,List]]) -> PandocMarkdown:
	"""given a processed bib entry, output a valid dendron file"""
	note : PandocMarkdown = PandocMarkdown.get_dendron_template()

	# add some metadata
	# TODO: keep the 'created' date and 'id' from old note?
	note.yaml_data['title'] = entry['title_txt']
	note.yaml_data['tags'] = entry['keywords_lst']
	note.yaml_data['attached_files'] = entry['files_lst']
	note.yaml_data['authors'] = entry['authors_lst']
	note.yaml_data['bibtex_key'] = entry['key']
	note.yaml_data['__bibtex__'] = entry

	# add things to the markdown body
	note.content = "\n".join([
		"",
		f"# {entry['title_txt']}",
		"",
		f"# file links:",
		"",
		"\n".join([
			f"- [{f}]({f})"
			for f in entry['files_lst']
		]),
		f"paper link: [{entry['title_txt']}]({entry['url']})" if 'url' in entry else "",
	])

	return note

def all_bib_to_dendron_vault(bib_filename : str, vault_prefix : str = '../../refs-vault/ref.'):
	"""given a bibtex file, output a vault of dendron notes"""
	db = load_bibtex(bib_filename)

	for key,val in db.items():
		note : PandocMarkdown = single_bib_to_dendron(val)
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


def test_bib_loader():
	db = load_bibtex('test.bib')
	
	# print(json.dumps(db, indent=2))
	print(yaml.safe_dump(db, default_flow_style=False))
	# for key,val in db.items():
	# 	print(key)
	# 	for k,v in val.items():
	# 		print("\t", k, v)
	# 		print(yaml.safe_dump(v, default_flow_style=False))
	# 	print(yaml.safe_dump(val, default_flow_style=False))


if __name__ == '__main__':
	import fire
	fire.Fire(all_bib_to_dendron_vault)









