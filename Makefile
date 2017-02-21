# Installs the package locally
install: uninstall package
	pip install dist/StudDP*.tar.gz

# Packs the package into the dist directory and signs it
package: clean
	python setup.py sdist
	gpg --detach-sign --armor dist/StudDP*.tar.gz

# Uninstalls the package from a local installation
uninstall:
	pip freeze | grep StudDP > /dev/null ; \
	if [ $$? -eq 0 ]; then \
		pip uninstall StudDP -y ; \
	fi

# Cleans up: Removes the packed package
clean:
	rm -rf dist
