from typing import *
import os
import time
from copy import deepcopy
import string
import random

# make sure the seed is random, for ID generation
random.seed(time.time())

import yaml

def keylist_access_nested_dict(
		d : Dict[str,Any], 
		keys : List[str],
	) -> Tuple[dict,str]:
	"""given a keylist `keys`, return (x,y) where x[y] is d[keys]
	by pretending that `d` can be accessed dotlist-style, with keys in the list being keys to successive nested dicts, we can provide both read and write access to the element of `d` pointed to by `keys`
	
	### Parameters:
	 - `d : Dict[str,Any]`
	   dict to access
	 - `keys : List[str]`   
	   list of keys to nested dict `d`
	
	### Returns:
	 - `Tuple[dict,str]` 
	   dict is the final layer dict which contains the element pointed to by `keys`, and the string is the last key in `keys`
	"""
	
	fin_dict : dict = d
	for k in keys[:-1]:
		if k in fin_dict:
			fin_dict = fin_dict[k]
		else:
			fin_dict[k] = {}
			fin_dict = fin_dict[k]
	fin_key = keys[-1]

	return (fin_dict,fin_key)



def gen_dendron_ID():
	"""generate a valid dendron ID
	
	should be 21 characters, alphanumeric
	"""
	
	return ''.join(random.choices(string.ascii_letters + string.digits, k = 21))



def fm_add_to_list(
		data : dict,
		keylist : List[str],
		insert_data : list,
	) -> dict:
	"""add things to the frontmatter
	
	given `keylist`, append to `data[keylist[0]][keylist[1]][...]` if it exists and does not contain `insert_data`
	if `data[keylist[0]][keylist[1]][...]` does not exist, create it and set it to `insert_data`
	"""
	fin_dict,fin_key = keylist_access_nested_dict(data,keylist)
	if fin_key not in fin_dict:
		fin_dict[fin_key] = insert_data
	else:
		for item in insert_data:
			if item not in fin_dict[fin_key]:
				fin_dict[fin_key].append(item)

	return data


def fm_add_bib(
		data : dict, 
		bibfiles : List[str] = ['../refs_miv.bib', '../refs_knc.bib'],
	) -> dict:
	"""add the bib files to the frontmatter
	
	we want it to look like
	```yaml
	bibliography: [../refs_miv.bib, ../refs_knc.bib]
	```
	"""

	return fm_add_to_list(
		data = data, 
		keylist = ['bibliography'], 
		insert_data = bibfiles,
	)

def fm_add_filters(
		data : dict, 
		filters : List[str] = ['$FILTERS$/dendron_links_md.py'],
	) -> dict:
	"""add the filters to the frontmatter

	we want it to look like
	```yaml
	__defaults__:
		filters:
			- $FILTERS$/dendron_links_md.py
	```
	"""

	return fm_add_to_list(
		data = data, 
		keylist = ['__defaults__', 'filters'], 
		insert_data = filters,
	)


DEFAULT_KEYORDER : List[str] = [
	'title',
	'desc',
	'id',
	'created',
	'updated',
	'bibliography',
	'__defaults__',
	'traitIds',
]

# for some reason, line breaks (such as in the middle of a list) are 
# either not handled properly by pyyaml, or not understood properly 
# by dendron's yaml parser. basically, yaml is weird and annoying.
# so, we set the width very high as a result to prevent this
DEFAULT_WRITER : Callable = lambda x : yaml.dump(x, default_flow_style = None, sort_keys = False, width = 9999)

class PandocMarkdown(object):
	def __init__(
			self, 
			delim : str = '---',
			loader : Callable[[str],dict] = yaml.safe_load,
			keyorder : List[str] = DEFAULT_KEYORDER,
			writer : Callable[[dict],str] = DEFAULT_WRITER,
		) -> None:
		
		self.delim : str = delim
		self.loader : Callable[[str],dict] = loader
		self.keyorder : List[str] = keyorder
		self.writer : Callable[[dict],str] = writer

		self.initialized : bool = False
		# get the first section and parse as yaml
		self.yaml_data : Dict[str, Any] = dict()
		# get the content
		self.content : str = ''

	def load(self, filename : str) -> None:
		"""load a file into the pandoc markdown object
		
		### Parameters:
		 - `filename : str`   
		   the filename to load
		"""

		with open(filename, "r", encoding = "utf-8") as f:
			# split the document by yaml file front matter
			sections : List[str] = f.read().split(self.delim)

		# check the zeroth section is empty
		if sections[0].strip():
			raise ValueError(f"file does not start with yaml front matter, found at start of file: {sections[0]}")
		
		if len(sections) < 3:
			raise ValueError(f'missing sections in file {filename}, check delims')

		# get the first section and parse as yaml
		self.yaml_data : Dict[str, Any] = self.loader(sections[1])
		# get the content
		self.content : str = self.delim.join(sections[2:])

		self.initialized : bool = True

	def update_time(self) -> None:
		"""updates the updated time in the frontmatter"""
		self.yaml_data['updated'] = int(time.time() * 1000)
	
	def dumps(self) -> str:
		if (self.yaml_data is None) or (self.content is None):
			raise Exception('')

		self.keyorder = self.keyorder + [
			k for k in self.yaml_data
			if k not in self.keyorder
		]
		
		# for k in self.keyorder:
		# 	if not (k in self.yaml_data):
		# 		raise KeyError(f'key {k} found in keyorder but not in yaml_data')

		self.yaml_data = {
			k : self.yaml_data[k]
			for k in self.keyorder
			if k in self.yaml_data
		}

		return '\n'.join([
			self.delim,
			self.writer(self.yaml_data).strip(),
			self.delim,
			self.content.lstrip(),
		])

	DEFAULT_FRONTMATTER : dict = {
		"bibliography": ["../refs_miv.bib", "../refs_knc.bib"],
		"__defaults__": {	"filters": ["$FILTERS$/get_markdown_links.py"]},
		"traitIds": ["journalNote"],
		"desc": '',
	}

	@staticmethod
	def get_dendron_template(fm : dict = DEFAULT_FRONTMATTER, do_id : bool = False) -> 'PandocMarkdown':
		file = PandocMarkdown()

		file.yaml_data = deepcopy(fm)
		currenttime : int = int(time.time() * 1000)
		file.yaml_data['created'] = currenttime
		file.yaml_data['updated'] = currenttime

		if do_id:
			file.yaml_data['id'] = gen_dendron_ID()

		return file

def modify_file_fm(file : str, apply_funcs : List[Callable]) -> None:
	pdm : PandocMarkdown = PandocMarkdown()
	pdm.load(file)

	for func in apply_funcs:
		pdm.yaml_data = func(pdm.yaml_data)
	
	with open(file, "w", encoding = "utf-8") as f:
		f.write(pdm.dumps())

def update_all_files_fm(
		dir : str,
		apply_funcs : List[Callable] = [fm_add_bib, fm_add_filters],
	) -> None:
	"""update the frontmatter of all files in a directory
	
	### Parameters:
	 - `dir : str`
	   the directory to update
	 - `apply_funcs : List[Callable]`   
	   list of functions to apply to the frontmatter
	"""

	for file in os.listdir(dir):
		if file.endswith(".md"):
			modify_file_fm(f'{dir}/{file}', apply_funcs)



