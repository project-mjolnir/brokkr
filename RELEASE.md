# Release instructions for Brokkr

## Perform pre-release tasks

1. Ensure ``MANIFEST.in``, ``setup.cfg`` and README/docs are up to date and commit any changes
2. Test the development version: ``brokkr monitor`` and ``brokkr start``
3. Close Github milestone (if open)
4. Check ``git status`` then ensure repo is up to date: ``hub sync`` (``git fetch upstream && git pull upstream master && git push origin master``)
5. Update version in ``brokkr/__init__.py`` to release version and add ``CHANGELOG.md`` entry


## Build and test

1. Activate the appropriate venv/Conda env: ``source env/bin/activate`` or ``conda activate ENV_NAME``
2. Update packaging packages: ``conda install wheel setuptools pip packaging` (if conda env) or ``pip install --upgrade setuptools wheel packaging`` (otherwise); then install build ``pip install --upgrade build pep517``
4. Build source and wheel distributions: ``python -m build``
5. In a clean env, install the build: ``pip install dist/brokkr-X.Y.Z.TAG-py3-none-any.whl``
6. Test the installed version: ``brokkr monitor`` and ``brokkr start``


## Upload to PyPI (production release)

1. Install/update Twine: ``conda install twine`` or ``pip install --upgrade twine``
2. Perform basic checks: ``twine check --strict dist/*``
3. Upload to TestPyPI first ``twine upload --repository testpypi dist/*``
4. In your development venv/conda env, download/install: ``pip install --index-url https://test.pypi.org/simple/ --no-deps brokkr``
5. Test the installed version: ``brokkr monitor`` and ``brokkr start``
6. Upload to live PyPI: ``twine upload dist/*``


## Execute release

1. Re-install dev build: ``pip install -e .``
2. Commit release: ``git commit -am "Release Brokkr version X.Y.Z"``
3. Tag release: ``git tag -a vX.Y.Z -m "Brokkr version X.Y.Z"``
4. If new major or minor version (X or Y in X.Y.Z), create release branch to maintain deployed version: ``git checkout -b X.Y.x && git push -u origin X.Y.x && git push upstream X.Y.z && git checkout master``
5. If release from ``master``, increment ``__version__`` in ``__init__.py`` to next expected release and add ``dev0`` (or ``dev<N+1>``, if a pre-release)
6. Commit change back to dev mode on ``master``: ``git commit -am "Begin development of version X.Y.x"``
7. Push changes upstream and to user repo: ``git push upstream master --follow-tags && git push origin master``
