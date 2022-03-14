# dendron-citations

tool for making [Dendron](https://www.dendron.so) work well with citing things using bibtex or Zotero

WORK IN PROGRESS. please use with care, since this will overwrite files in your dendron vault


# [`refs_vault_gen.py`](refs_vault_gen.py)

generates a vault of dendron notes corresponding to entries from a bibtex file

this allows the user to reference the dendron notes instead of raw bibtex item (such as when using [PandocCiter](https://github.com/notZaki/PandocCiter)), which lets us use backlink features from dendron to see where we have cited a paper

> Note: I personally put all my references in a separate vault from my main vault, to avoid clutter. I highly recommend this, since this *might* also prevent you from accidentally overwriting things in your main vault.

## Usage: 

```bash
python refs_vault_gen.py --bib_filename <bibtex_file> --vault_loc <output_dir>
```
or simply
```bash
python refs_vault_gen.py <bibtex_file> <output_dir>
```

### Example:

for example, if the script and a bibtex file `refs.bib` are both located in the directory containing our `vault/`, we may write
```bash
python refs_vault_gen.py refs.bib vault/refs.
```
this will create notes of the form `refs.some-bibtex-key.md` in the `vault/` directory.

Given the bibtex file `examples/refs.bib`, the vault `examples/vault/` was generated with
```bash
py refs_vault_gen.py examples/refs.bib examples/vault/refs.
```


## tag notes

Not only can we use dendron backlinks to view where we have cited a certain paper, but we can additionally use the backlinks to see all papers by a given author, or all papers with a given keyword!

The argument `--make_tag_notes`, `True` by default, will enable the generation of notes for each tag, as long as the tag does not yet exists. Keywords will be processed into tags by removing spaces and other extra characters. Author tags will be of the format `<first_char_of_first_name>-<last_name>`, with all characters converted to ascii. The actual notes for author tags will contain the full author names.

## templates

For now, you need to manually modify the template string `DEFAULT_TEMPLATE` in the file `refs_vault_gen.py` to suit your needs. The template is in [Mustache](https://mustache.github.io) format, with some extensions:

- Add the prefix `_bln_` to the name of any iterable variable to get access to a boolean value that is true if the variable is not empty
- Lists of non-dict items are turned into lists of dicts, where each dict has a single key `elt` with the value of the item


# Installation:

not yet on pypi. for now, you just need the files [`md_util.py`](md_util.py) and [`refs_vault_gen.py`](refs_vault_gen.py) somewhere, along with the dependencies listed below. This is a WORK IN PROGRESS, so I haven't put much work into streamlining installation.

you can install the requirements with
```bash
pip install -r requirements.txt
```

## Dependencies:

- https://github.com/t-wissmann/biblib
	- not on pypi, installed from git repo
	- note: forked from https://github.com/aclements/biblib, which no longer works
- [`pyyaml`](https://github.com/yaml/pyyaml/)
- [`chevron`](https://github.com/noahmorrison/chevron)
	- python implementation of the [mustache](https://mustache.github.io) templating language
- [`pypandoc`](https://github.com/NicklasTegner/pypandoc) (optional)
	- for converting notes to markdown



# Roadmap:

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
- [ ] turn this into a real vscode plugin
	- mostly to simplify installation 
	- will probably use [`vscode-ext`](https://github.com/CodeWithSwastik/vscode-ext)

## zotero integration

do everything as for bibtex integration, but also:

- [ ] add links/copies in zotero to the dendron notes (when they exist)
- [ ] have zotero item materials inside dendron file
	- zotero notes, plaintext attachments inline
	- links to all other attachments
	- exclude the dendron file to avoid recursion, haha

# Misc

- to allow simpler references to papers in a separate vault, without having to type `[[dendron://refs-vault/<bibtex key>]]`, the user may create a vscode snippet in `> Preferences > Configure User Snippets > markdown.json`

```json
"dendron-cite": {
	"prefix": "@",
	"body": [
		"[[dendron://refs-vault/refs.$1]]"
	],
	"description": "dendron reference citation"
},
```
