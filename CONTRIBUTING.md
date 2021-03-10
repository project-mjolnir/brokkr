# Brokkr Contributing Guide

Brokkr is part of Project Mjolnir, and is developed with standard Github flow. You should be familiar with the basics of using


## Reporting issues

Discover a bug? Want a new feature? Open an issue! Make sure to describe in detail, with reproducible examples and references if possible, what you are looking to have fixed/added.
While we can't promise we'll fix everything you might find, we'll certainly take it into consideration, and typically welcome pull requests to resolve accepted issues.
Thanks!



## Setting Up a Development Environment

### Forking and cloning the repo

First, navigate to the [Brokkr repo](https://github.com/project-mjolnir/brokkr) in your web browser and press the ``Fork`` button to make a personal copy of the repository on your own Github account.
Then, click the ``Clone or Download`` button on your repository, copy the link and run the following on the command line to clone the repo:

```bash
git clone <LINK-TO-YOUR-REPO>
```

Finally, set the upstream remote to the official Brokkr repo with:

```bash
git remote add upstream https://github.com/project-mjolnir/brokkr.git
```

### Creating a conda environment or virtualenv

If you use Anaconda, you can create a conda environment with the following commands:

```bash
conda create -n brokkr-dev python=3
conda activate brokkr-dev
```

Otherwise, you can create a `venv`:

```bash
python3 -m venv brokkr-dev
source brokkr-dev/bin/activate
```


### Installing and running brokkr

Finally, `cd` to the directory where your git clone is stored and install it:

```bash
cd brokkr
pip install -e .[all]
```

You can then run Brokkr as normal, with the ``brokkr`` command.
When you make changes in your local copy of the Brokkr git repository, they will be reflecting in your installed copy of Brokkr as soon as you re-run it.

On Windows and Mac, use of Anaconda/Miniconda is recommended, though not required.
While these platforms are supported for development, some install and system-management functionality specific to running Brokkr in production may be unavailable.



## Brokkr Branches

When you start to work on a new pull request (PR), you need to be sure that your work is done on top of the correct Brokkr branch, and that you base your PR on Github against it.

To guide you, issues on Github are marked with a milestone that indicates the correct branch to use. If not, follow these guidelines:

* Use the latest release branch (e.g. `0.3.x` for bugfixes only (*e.g.* milestones `v0.3.1` or `v0.3.2`)
* Use `master` to introduce new features or break compatibility with previous Brokkr versions (*e.g.* milestones `v0.4alpha2` or `v0.4beta1`).

You should also submit bugfixes to the release branch or `master` for errors that are only present in those respective branches.



## Submitting a PR

To start working on a new PR, you need to execute these commands, filling in the branch names where appropriate (``<BASE-BRANCH>`` is the branch you're basing your work against, e.g. ``master``, while ``<FEATURE-BRANCH>`` is the branch you'll be creating to store your changes, e.g. ``fix-startup-bug`` or ``add-uart-support``:

```bash
$ git checkout <BASE-BRANCH>
$ git pull upstream <BASE-BRANCH>
$ git checkout -b <FEATURE-BRANCH>
```

Once you've made and tested your changes, commit them with a descriptive message of 74 characters or less written in the imperative tense, with a capitalized first letter and no period at the end. For example:

```bash
git commit -am "Fix bug reading uart device on Windows"
```

Finally, push them to your fork, and create a pull request to the project-mjolnir/brokkr repository on Github:

```bash
git push -u origin <FEATURE-BRANCH>
```

That's it!
