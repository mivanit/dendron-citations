SOURCE = $(wildcard dendron_citations/*.py)
ENV = env

# block separator
BSP = "======================================================================"

# PYLINT_OPTIONS = --disable=invalid-name,bad-indentation,use-list-literal,use-dict-literal,superfluous-parens,trailing-whitespace,trailing-newlines,too-many-instance-attributes
PYLINT_OPTIONS = --disable=invalid-name,bad-indentation,use-list-literal,use-dict-literal,superfluous-parens,trailing-whitespace,trailing-newlines,too-many-instance-attributes,missing-function-docstring,wrong-import-position

# detecting os
ifeq ($(OS),Windows_NT)
	detected_os = Windows
	FLAG_PTHREAD = -lpthread
else
	detected_os = Linux
	FLAG_PTHREAD = -pthread
endif


.PHONY: setup_env
setup_env:
	@echo "# set up virtual environment, installing dependecies and the package"
	
	@printf "$(BSP)\n# setting up virtual environment  \n$(BSP)\n"
	python -m venv env

	@printf "$(BSP)\n# installing dev dependencies  \n$(BSP)\n"
	$(ENV)/Scripts/pip install -r requirements_dev.txt

	@printf "$(BSP)\n# installing package  \n$(BSP)\n"
	$(ENV)/Scripts/pip install -e .

# @printf "$(BSP)\n# installing package dependencies  \n$(BSP)\n"
# $(ENV)/Scripts/pip install -r requirements.txt


	@printf "$(BSP)\n# installation complete!  \n$(BSP)\n"

.PHONY: env_clean
env_clean:
	@echo "# clean up the existing virtual environment"
	
	rm -rf $(ENV)/

.PHONY: check
check:
	@echo "# run mypy, pylint"

	@echo "# will run on files:"
	@echo "$(SOURCE)"
	
	@printf "$(BSP)\n# running mypy  \n$(BSP)\n"
	$(ENV)/Scripts/mypy $(SOURCE)

	@printf "$(BSP)\n# running pylint  \n$(BSP)\n"
	$(ENV)/Scripts/pylint $(SOURCE) $(PYLINT_OPTIONS)

	@printf "$(BSP)\n# type checking complete!  \n$(BSP)\n"

# @echo "$(BLOCKSEP)"
# @echo "# running pytype"
# @echo "$(BLOCKSEP)"
# -pytype $(SOURCE)



	


# listing targets, from stackoverflow
# https://stackoverflow.com/questions/4219255/how-do-you-get-the-list-of-targets-in-a-makefile
.PHONY: help
help:
	@echo -n "# Common make targets"
	@echo ":"
	@cat Makefile | sed -n '/^\.PHONY: / h; /\(^\t@*echo\|^\t:\)/ {H; x; /PHONY/ s/.PHONY: \(.*\)\n.*"\(.*\)"/    make \1\t\2/p; d; x}'| sort -k2,2 |expand -t 20

	@echo "# detected source files:"
	@echo "    $(SOURCE)"

	@echo "# activate env using:"
	@echo "    source $(ENV)/Scripts/activate"
