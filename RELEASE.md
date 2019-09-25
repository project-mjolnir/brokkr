# Release instructions for Brokkr

1. Ensure ``MANIFEST.in``, metadata, trove classifiers and Readme/docs are up to date
2. Check import (``import brokkr; brokkr.__version__``) and if present, run tests
3. Close Github milestone (if open)
4. Check ``git status`` then ensure repo is up to date: ``git sync`` (``git fetch upstream && git pull upstream master && git push origin master``)
5. Ensure any untracked local files are eliminated: ``git clean -xfdi``
6. Update version in ``brokkr/_version.py`` to release version and ``CHANGELOG.md`` as necessary
7. Commit changes: ``git commit -am "Release Brokkr version X.Y.Z"``
8. Activate the appropriate venv/Conda env: ``source env/bin/activate`` or ``conda activate ENV_NAME``
9. Update packaging packages: ``conda install wheel setuptools pip`` (if conda env) or ``pip install --upgrade setuptools wheel`` (otherwise)
10. Build source and wheel distributions: ``python setup.py sdist bdist_wheel``
11. Install/update Twine if uploading to PyPI: ``conda install twine`` or ``pip install --upgrade twine``
12. Upload to TestPyPI first (if uploading to PyPI) ``python -m twine --repository-url https://test.pypi.org/legacy/ upload dist/*`` (note: legacy is current API)
13. In a clean venv/conda env, test download/install: ``pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple brokkr`` (if PyPI) or ``pip install .`` (otherwise)
14. In test env, check import (``import brokkr; brokkr.__version__``) and run tests
15. Upload to live PyPI (if uploading to PyPI): ``python -m twine upload dist/*``
16. Tag release: ``git tag -a vX.Y.Z -m "Brokkr version X.Y.Z"``
17. Clean release files: ``git clean -xfd``
18. If new minor version, create release branch ``vX.Y`` to maintain deployed version
19. If new minor version, in ``master`` branch update ``brokkr/_version.py`; increment minor and add ``dev0``
20. Commit change back to dev mode on ``master``: ``git commit -am "Begin development of X.Y"``
21. Push changes upstream and to user repo: ``git push upstream master --follow-tags && git push origin master``
