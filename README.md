# dendron-citations

tool for making [Dendron](https://www.dendron.so) work well with citing things using bibtex or Zotero

WORK IN PROGRESS. please use with care, since this will overwrite files in your dendron vault

The main script is [`dendron_gen_refs.py`](scripts/dendron_gen_refs.py), which generates a vault of dendron notes corresponding to entries from a bibtex file

this allows the user to reference the dendron notes instead of raw bibtex item (such as when using [PandocCiter](https://github.com/notZaki/PandocCiter)), which lets us use backlink features from dendron to see where we have cited a paper

> Note: I personally put all my references in a separate vault from my main vault, to avoid clutter. I highly recommend this, since this *might* also prevent you from accidentally overwriting things in your main vault.


# Contents:
- [Usage](#usage)
- [Installation](#installation)
- [Extras](#extras)
- [Roadmap](#roadmap)



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

Or, we could create a config file such as [`examples/custom_cfg.json`](examples/custom_cfg.json) and pass it in as
```bash
dendron_gen_refs.py gen <path_to_config_file>
```

> **Note:** if you pass a config file, the script will change its directory to that of the config file, to allow paths to be specified relative to that file.



# Installation:

Not yet on [PyPi](https://pypi.org/), due to instability. you can install with
```bash
pip install -e git+https://github.com/mivanit/dendron-citations.git#egg=dendron_citations
```

Note that this will place an executable `dendron_gen_refs.py` in your python `Scripts` folder (and thus hopefully in your path).

## Dependencies:

- https://github.com/t-wissmann/biblib
	- not on pypi, installed from git repo
	- note: forked from https://github.com/aclements/biblib, which no longer works
- [`pyyaml`](https://github.com/yaml/pyyaml/)
- [`chevron`](https://github.com/noahmorrison/chevron)
	- python implementation of the [mustache](https://mustache.github.io) templating language
- [`pypandoc`](https://github.com/NicklasTegner/pypandoc) (optional)
	- for converting notes to markdown







# Extras

## tag notes

Not only can we use dendron backlinks to view where we have cited a certain paper, but we can additionally use the backlinks to see all papers by a given author, or all papers with a given keyword!

The argument `--make_tag_notes`, `True` by default, will enable the generation of notes for each tag, as long as the tag does not yet exists. Keywords will be processed into tags by removing spaces and other extra characters. Author tags will be of the format `<first_char_of_first_name>-<last_name>`, with all characters converted to ascii. The actual notes for author tags will contain the full author names.

## templates

For now, you need to manually modify the template string `DEFAULT_TEMPLATE` in the file `refs_vault_gen.py` to suit your needs. The template is in [Mustache](https://mustache.github.io) format, with some extensions:

- Add the prefix `_bln_` to the name of any iterable variable to get access to a boolean value that is true if the variable is not empty
- Lists of non-dict items are turned into lists of dicts, where each dict has a single key `elt` with the value of the item

For example, if `keywords` is a list of strings `['a', 'b']`, we can use the template
```mustache
{{#_bln_keywords}}# Keywords
{{/_bln_keywords}}
{{#keywords}}
 - #{{elt}}
{{/keywords}}
```

to print
```markdown
# Keywords
 - a
 - b
```

or to return an empty string (with newlines) if `keywords` is empty.

## vscode task

in order to have a vscode shortcut to running the `dendron_gen_refs.py` script, we can take advantage of [VSCode Tasks](https://code.visualstudio.com/docs/editor/tasks) and add the following task to `.vscode/tasks.json`:

```json
{
	"label": "dendron-citations",
	"type": "shell",
	"command": "dendron_gen_refs.py {{your_config_file}}",
}
```

where `{{your_config_file}}` is the path to your config file relative to the root of the workspace -- for example, `examples/custom_cfg.json`



## cross-vault links snippet

to allow simpler references to papers in a separate vault, without having to type `[[dendron://refs-vault/<bibtex key>]]`, the user may create a vscode snippet in `> Preferences > Configure User Snippets > markdown.json`

```json
"dendron-cite": {
	"prefix": "@",
	"body": [
		"[[dendron://refs-vault/refs.$1]]"
	],
	"description": "dendron reference citation"
},
```




# Roadmap:

## general
- [x] implement a configuration system
- [x] set up as an installable package
- [ ] turn this into a real vscode plugin
	- will probably use [`vscode-ext`](https://github.com/CodeWithSwastik/vscode-ext)

## bibtex integration

- [x] given a bibtex file, generate a vault of dendron notes bibtex keys as filenames
- [x] add tags and other things from bibtex to metadata
- [x] optional generation of tag files
- [ ] "beneath" each note for the bibtex, add another note for the citation itself.
	- note that this will all break if the bibtex keys change!
- [ ] automatically convert [PandocCiter](https://github.com/notZaki/PandocCiter) style 
	- this will allow for better searching for papers
- [ ] make citations work properly when compiling with [Pandoc](https://pandoc.org/)
	- probably best to do this as part of [dendron-pandoc](https://github.com/mivanit/dendron-pandoc)

## zotero integration

do everything as for bibtex integration, but also:

- [ ] add links/copies in zotero to the dendron notes (when they exist)
- [ ] have zotero item materials inside dendron file
	- zotero notes, plaintext attachments inline
	- links to all other attachments
	- exclude the dendron file to avoid recursion, haha


# Developing:

After cloning, run
```bash
make help
```
to see some utilities for developing (setting up a virtual environment, running type and style checkers, etc.)




