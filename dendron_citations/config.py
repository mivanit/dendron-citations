"""handling configuation and defaults for dendron_citations"""

# standard library imports
from typing import (
	Optional, Dict,
)

import os
import sys
from dataclasses import dataclass

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
