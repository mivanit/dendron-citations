"""generate a vault of dendron notes from entries in a bibtex file
# Usage: 

to generate reference notes, run from anywhere:

```bash
dendron_gen_refs.py [cfg_path] [--<kwarg>=<val>]
```

## Help and configuration

- `--help` : print help message and exit:
```bash
dendron_gen_refs.py --help
```

- `--print_cfg` : print to console an example config in either json or yaml (json by default):

```bash
dendron_gen_refs.py --print_cfg [--fmt=<format>]
```

## Generation:

when running
```bash
dendron_gen_refs.py [cfg_path] [**kwargs]
```

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

## Examples:

```bash
dendron_gen_refs.py gen --bib_filename=<bibtex_file> --vault_loc=<output_dir>
```

Or, we could create a config file such as 
[`examples/custom_cfg.json`](examples/custom_cfg.json)
and pass it in as
```bash
dendron_gen_refs.py gen <path_to_config_file>
```

> **Note:** if you pass a config file, the script will change its directory 
to that of the config file, to allow paths to be specified relative to that file.

"""

# pylint: disable=invalid-name, bad-indentation

# standard library imports
from typing import (
	Optional, Any,
	Dict, List,
)

import os
import sys
import json

# package imports
import yaml # type: ignore
import biblib.bib # type: ignore

# local imports
from dendron_citations.dc_util import (
	OrderedDictType,
)
from dendron_citations.md_util import PandocMarkdown,gen_dendron_ID
from dendron_citations.bibtex_util import load_bibtex_raw
from dendron_citations.process_meta import Config,GLOBAL_AUTHORS_DICT
from dendron_citations.citationentry import CitationEntry






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
		if cfg_dir != '':
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









