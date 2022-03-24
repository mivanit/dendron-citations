
import vscode

from dendron_citations.refs_vault_gen import gen

vscfg_cfg_path = vscode.Config(
	name = 'dendron_citations_cfg_path', 
	description = 'configuration file path for dendron_citations', 
	input_type = str, 
	default = "dc_config.json",
)

ext : vscode.Extension = vscode.Extension(
	name = "dendron_citations",
	display_name = "dendron_citations",
	version = 'v0.0.1',
	config = [vscfg_cfg_path],
)

@ext.event
async def on_activate():
	vscode.log(f"The Extension '{ext.name}' has started")
	vscode.InfoMessage(f"'{ext.name}' has started")
	# await # TODO

@ext.command(name = "Generate Dendron citation notes")
async def gen_notes(ctx):
	gen(cfg_path = vscfg_cfg_path.value)
	return await ctx.show(vscode.InfoMessage(f"{ext.name} is generating citation notes..."))



vscode.build(ext)

