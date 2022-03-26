SOURCE = $(wildcard dendron_citations/*.py)
ENV = env

# block separator
BSP = "======================================================================"

# PYLINT_OPTIONS = --disable=invalid-name,bad-indentation,use-list-literal,use-dict-literal,superfluous-parens,trailing-whitespace,trailing-newlines,too-many-instance-attributes
PYLINT_OPTIONS = --disable=invalid-name,bad-indentation,use-list-literal,use-dict-literal,superfluous-parens,trailing-whitespace,trailing-newlines,too-many-instance-attributes,missing-function-docstring,wrong-import-position,fixme

# detecting os
ifeq ($(OS),Windows_NT)
	detected_os = Windows
	ENV_PATH = $(ENV)/Scripts
else
	detected_os = Linux
	ENV_PATH = $(ENV)/bin
endif


.PHONY: setup_env
setup_env:
	@echo "# set up virtual environment, installing dependecies and the package"
	
	@printf "$(BSP)\n# setting up virtual environment  \n$(BSP)\n"
	python -m venv env

	@printf "$(BSP)\n# installing dev dependencies  \n$(BSP)\n"
	$(ENV_PATH)/pip install -r requirements_dev.txt

	@printf "$(BSP)\n# installing package  \n$(BSP)\n"
	$(ENV_PATH)/pip install -e .

# @printf "$(BSP)\n# installing package dependencies  \n$(BSP)\n"
# $(ENV_PATH)/pip install -r requirements.txt


	@printf "$(BSP)\n# installation complete!  \n$(BSP)\n"

.PHONY: env_clean
env_clean:
	@echo "# clean up the existing virtual environment"
	
	rm -rf $(ENV_PATH)/

.PHONY: check
check:
	@echo "# run mypy, pylint"

	@echo "# will run on files:"
	@echo "$(SOURCE)"
	
	@printf "$(BSP)\n# running mypy  \n$(BSP)\n"
	$(ENV_PATH)/mypy $(SOURCE)

	@printf "$(BSP)\n# running pylint  \n$(BSP)\n"
	$(ENV_PATH)/pylint $(SOURCE) $(PYLINT_OPTIONS)

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

	@printf "\n# detected source files:\n"
	@echo "    $(SOURCE)"


	@printf "\n# detected os:"
	@echo "    $(OS)    ($(detected_os))"

	@printf "\n# activate env using:\n"
	@echo "    source $(ENV_PATH)/activate"
