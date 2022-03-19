import setuptools
import pkg_resources

with open("README.md", "r", encoding="utf-8") as fh:
    long_description : str = fh.read()

def get_requirements() -> list:
    """Return requirements as list
	
	from: https://stackoverflow.com/questions/69842651/parse-error-in-pip-e-gith-expected-wabcd
	"""
    with open('requirements.txt') as f:
        packages : list = []
        for line in f:
            line = line.strip()
            # let's also ignore empty lines and comments
            if not line or line.startswith('#'):
                continue
            if 'https://' in line:
                # tail = line.rsplit('/', 1)[1]
                # tail = tail.split('#')[0]
                # line = tail.replace('@', '==').replace('.git', '')
                if (line.count('#egg=') != 1) or (not line.startswith('-e ')):
                    raise ValueError(f'cant parse required package: {line}')

                pckgname : str = line.split('#egg=')[-1]

                line = pckgname + ' @ ' + line.split('-e ', 1)[-1].strip()

            packages.append(line)
    return packages

setuptools.setup(
    name = "dendron_citations",
    version = "0.0.1",
    author = "Michael Ivanitskiy",
    author_email = "mivanits@umich.edu",
    description = "tool for making dendron work well with citing things using bibtex or Zotero",
    long_description = long_description,
    long_description_content_type = "text/markdown",
	install_requires = get_requirements(),
	scripts = ['scripts/dendron_gen_refs.py'],
    url = "https://github.com/mivanit/dendron-citations",
    project_urls = {
        "Bug Tracker": "https://github.com/mivanit/dendron-citations/issues",
    },
	classifiers = [
        "Programming Language :: Python :: 3.8",
		"Programming Language :: Python :: 3.9",
		"Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: GPL-3.0 License",
        "Operating System :: OS Independent",
    ],
    packages = ["dendron_citations"],
    python_requires = ">=3.8",
	keywords = "dendron markdown notes citations bibtex zotero",
)