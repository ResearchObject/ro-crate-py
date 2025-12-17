# Contributing to this repository

ro-crate-py is open source software distributed under the Apache License, Version 2.0. Contributions are welcome, but please read this guide first. Submitted contributions are assumed to be covered by section 5 of the [license](LICENSE).


## Before you begin

[Set up Git](https://docs.github.com/en/github/getting-started-with-github/set-up-git) on your local machine, then [fork](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo) this repository on GitHub and [create a local clone of your fork](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#step-2-create-a-local-clone-of-your-fork).

For instance, if your GitHub user name is `simleo`, you can get a local clone as follows:

```
$ git clone https://github.com/simleo/ro-crate-py
```

You can see that the local clone is pointing to your remote fork:

```
$ cd ro-crate-py
$ git remote -v
origin	https://github.com/simleo/ro-crate-py (fetch)
origin	https://github.com/simleo/ro-crate-py (push)
```

To keep a reference to the original (upstream) repository, you can add a remote for it:

```
$ git remote add upstream https://github.com/researchobject/ro-crate-py
$ git fetch upstream
```

This allows, among other things, to easily keep your fork synced to the upstream repository through time. For instance, to sync your `master` branch:

```
$ git checkout master
$ git fetch -p upstream
$ git merge --ff-only upstream/master
$ git push origin master
```

If you need help with Git and GitHub, head over to the [GitHub docs](https://docs.github.com/en/github). In particular, you should be familiar with [issues and pull requests](https://docs.github.com/en/github/collaborating-with-issues-and-pull-requests).


## Making a contribution

Contributions can range from fixing a broken link or a typo in the documentation to fixing a bug or adding a new feature to the software. Ideally, contributions (unless trivial) should be related to an [open issue](https://github.com/researchobject/ro-crate-py/issues). If there is no existing issue or [pull request](https://github.com/researchobject/ro-crate-py/pulls) related to the changes you wish to make, you can open a new one.

Make your changes on a branch in your fork, then open a pull request (PR). Please take some time to summarize the proposed changes in the PR's description, especially if they're not obvious. If the PR addresses an open issue, you should [link it to the issue](https://docs.github.com/en/github/managing-your-work-on-github/linking-a-pull-request-to-an-issue).


## Contributing documentation

Currently, documentation consists of a few [Markdown](http://daringfireball.net/projects/markdown) files such as this one. Read the [Mastering Markdown](https://guides.github.com/features/mastering-markdown) guide for a quick introduction to the format. Before opening the PR, you can check that the document renders as expected by looking at the corresponding page on the relevant branch in your fork.


## Contributing software

ro-crate-py is written in [Python](https://www.python.org). To isolate your development environment from the underlying system, you can use a [virtual environment](https://docs.python.org/3.8/library/venv.html):

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install --upgrade pip
$ pip install -r requirements.txt
```

For development, it's recommended to install ro-crate-py in [editable mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html):

```
pip install -e .
```

In this way, any changes to the code will be picked up immediately, without the need to reinstall the package.

When you're done with your work, you can deactivate the virtual environment by typing `deactivate` on your shell.

Before pushing any changes, make sure everything is fine by running the linting and testing commands as explained below.

### Linting

ro-crate-py uses [Flake8](https://github.com/PyCQA/flake8) for linting. The configuration is in `setup.cfg` and it's picked up automatically. If you have a `venv` directory or any other directory you don't want to be checked by Flake8, use the `--exclude` option.

```
pip install flake8
flake8 --exclude venv ./
```

### Pre-commit hooks
ro-crate-py comes with a configuration file for [pre-commit](https://github.com/pre-commit/pre-commit) `.pre-commit-config.yaml`.
This configuration file defines so-called "hooks" which are executed upon each commit, to automatically format the code in the commited files according to the requirements defined for instance in the flake8 configuration file (e.g removing spaces from blank lines...).

To benefit from these automated hooks, you need first to install the pre-commit package.
`pip install pre-commit`

The hooks should then be installed once for your local copy of the repository by running the following command in the root of the repo.
`pre-commit install`

Once installed the hooks will be executed each time a new commit is made, for the files being commited.
If some checks failed or could not be fixed automatically, an error message will be shown and the commit will be aborted.

While not recommended, you can bypass the hooks by passing the additional flag `--no-verify` to the `git commit` command.

Some IDEs have plugins for precommit (e.g [here](https://marketplace.visualstudio.com/items?itemName=elagil.pre-commit-helper) for VSCode), which would for instance run the hooks for the currently opened file each time it is saved. The plugins typically pick up the configuration file automatically.

### Testing

Testing is done with [pytest](https://pytest.org):

```
pip install pytest
pytest test
```

If a test is failing, you can get more information by enabling verbose mode and stdout/stderr dump. For instance:

```
pytest -sv test/test_write.py::test_remote_uri_exceptions
```

Ideally, every code contribution should come with new unit tests that add coverage for the bug fix or new feature.

### Using the Docker image for development

ro-crate-py is currently a fairly simple library that does not require any special infrastructure setup, so virtual environments should be enough for development. However, if you want a higher degree of isolation, you can build the [Docker](https://www.docker.com/) image with:

```
docker build -t ro-crate-py .
```

And then run it interactively with:

```
docker run --rm -it --name ro-crate-py ro-crate-py bash
```


## Tidying up after PR merge

After your PR has been merged, you can delete the branch used for your changes. You can delete the remote branch from GitHub, by clicking on "Delete branch" in the PR's page. To resync everything, run:

```
git checkout master
git fetch -p upstream
git merge --ff-only upstream/master
git push origin master
git branch -d <pr_branch_name>
```
