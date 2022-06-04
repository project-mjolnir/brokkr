# Contributing Guide

Brokkr is part of Project Mjolnir, and is developed with standard GitHub flow.

If you're not comfortable with at least the basics of ``git`` and GitHub, we recommend reading beginner tutorials such as [GitHub's Git Guide](https://github.com/git-guides/), its [introduction to basic Git commands](https://guides.github.com/introduction/git-handbook/#basic-git) and its [guide to the fork workflow](https://guides.github.com/activities/forking/), or (if you prefer) their [video equivalents](https://www.youtube.com/githubguides).
However, this contributing guide should fill you in on most of the basics you need to know.

Let us know if you have any further questions, and we look forward to your contributions!


## Reporting Issues

Discover a bug?
Want a new feature?
[Open](https://github.com/project-mjolnir/brokkr/issues/new/choose) an [issue](https://github.com/project-mjolnir/brokkr/issues)!
Make sure to describe the bug or feature in detail, with reproducible examples and references if possible, what you are looking to have fixed/added.
While we can't promise we'll fix everything you might find, we'll certainly take it into consideration, and typically welcome pull requests to resolve accepted issues.



## Setting Up a Development Environment

**Note**: You may need to substitute ``python3`` for ``python`` in the commands below on some Linux distros where ``python`` isn't mapped to ``python3`` (yet).


### Fork and clone the repo

First, navigate to the [project repository](https://github.com/project-mjolnir/brokkr) in your web browser and press the ``Fork`` button to make a personal copy of the repository on your own GitHub account.
Then, click the ``Clone or Download`` button on your repository, copy the link and run the following on the command line to clone the repo:

```shell
git clone <LINK_TO_YOUR_REPO>
```

Finally, set the upstream remote to the official Brokkr repo with:

```shell
git remote add upstream https://github.com/project-mjolnir/brokkr.git
git fetch --all
```


### Create and activate a fresh environment

Particularly for development installs, we highly recommend you create and activate a virtual environment to avoid any conflicts with other packages on your system or causing any other issues.
Of course, you're free to use any environment management tool of your choice (conda, virtualenvwrapper, pyenv, etc).

To do so with Conda (recommended), simply execute the following:

```shell
conda create -c conda-forge -n brokkr-env python=3.9
```

And activate it with

```shell
conda activate brokkr-env
```

With pip/venv, you can create a virtual environment with

```shell
python -m venv brokkr-env
```

And activate it with the following on Linux and macOS,

```shell
source brokkr-env/bin/activate
```

or on Windows (cmd),

```cmd
.\brokkr-env\Scripts\activate.bat
```

Regardless of the tool you use, make sure to remember to always activate your environment before using it.


### Install Brokkr in editable mode

Then, to install the Brokkr package and its dependencies in editable ("development") mode, where updates to the source files will be reflected in the installed package, and include any additional dependencies used for development, run

```shell
cd brokkr
python -m pip install -e .[all]
```

You can then import and run Brokkr as normal, with the ``brokkr`` command (or ``python -m brokkr``).
When you make changes in your local copy of the git repository, they will be reflected in your installed copy as soon as you re-run Python.

On Windows and Mac, use of Anaconda/Miniconda is recommended, though not required.
While these platforms are supported for development, some install and system-management functionality specific to running Brokkr in production may be unavailable.



## Deciding Which Branch to Target

When you start to work on a new pull request (PR), you need to be sure that your work is done on top of the correct branch, and that you base your PR on GitHub against it.

To guide you, issues on GitHub are typically marked with a milestone that indicates the correct branch to use.
If not, follow these guidelines:

* Use the latest release branch for bugfixes only (e.g. ``0.3.x``, with milestones ``v0.3.1`` or ``v0.3.x``)
* Use ``master`` to introduce new features or break compatibility with previous Brokkr versions (e.g. milestones ``v0.4alpha2`` or ``v0.4.0``).

Of course, for issues that are only present in those respective branches, target your PRs against that specific branch.



## Making Your Changes

To start working on a new PR, you need to execute these commands, filling in the branch names where appropriate (``<BASE-BRANCH>`` is the branch you're basing your work against, e.g. ``master``, while ``<FEATURE-BRANCH>`` is the branch you'll be creating to store your changes, e.g. ``fix-startup-bug`` or ``add-widget-support``:

```bash
git checkout <BASE-BRANCH>
git pull upstream <BASE-BRANCH>
git checkout -b <FEATURE-BRANCH>
```

Once you've made and tested your changes, commit them with a descriptive, unique message of 74 characters or less written in the imperative tense, with a capitalized first letter and no period at the end.
Try to make your commit message understandable on its own, giving the reader a high-level idea of what your changes accomplished without having to dig into the diffs.
For example:

```bash
git commit -am "Fix bug reading env variable when importing package on Windows"
```

If your changes are complex (more than a few dozen lines) and can be broken into discrete steps/parts, its often a good idea to make multiple commits as you work.
On the other hand, if your changes are fairly small (less than a dozen lines), its usually better to make them as a single commit, and then use the ``git -a --amend`` (followed by ``git push -f``, if you've already pushed your work) if you spot a bug or a reviewer requests a change.

These aren't hard and fast rules, so just use your best judgment, and if there does happen to be a significant issue we'll be happy to help.


## Testing your Work

While a formal test suite for the project is still in work, you should still test them locally, and on a deployed installation if possible.
For the former, make sure that ``brokkr status``/``brokkr monitor`` displays correctly, ``brokkr --mode test start`` runs without unexpected errors, and that any commands relevant to your work function as intended.
If an error occurs, adding one or more ``-v`` verbose flags, or using the ``--log-level-file`` and ``--log-level-console`` options are very helpful for debugging.



## Pushing your Changes and Submitting a Pull Request

Now that your changes are ready to go, you'll need to push them to the appropriate remote.
All contributors, including core developers, should push to their personal fork and submit a PR from there, to avoid cluttering the upstream repo with feature branches.
To do so, run:

```bash
git push -u origin <FEATURE-BRANCH>
```

Where ``<FEATURE-BRANCH>`` is the name of your feature branch, e.g. ``fix-startup-bug``.

Finally, create a pull request to the [project-mjolnir/brokkr repository](https://github.com/project-mjolnir/brokkr/) on GitHub.
Make sure to set the target branch to the one you based your PR off of (``master`` or ``X.x``).
We'll then review your changes, and after they're ready to go, your work will become an official part of Brokkr.

Thanks for taking the time to read and follow this guide, and we look forward to your contributions!
