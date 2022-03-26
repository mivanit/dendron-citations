"""generate dendron reference notes from bibtex
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
"""

from dendron_citations.refs_vault_gen import main

import fire
fire.Fire(main)