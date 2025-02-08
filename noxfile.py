import nox


# @nox.session(python='3.12')
# def flake8(session):
#     session.install('.', '.[dev]')
#     session.run('flake8', '--extend-ignore=E501,E125,E128', '--extend-exclude=.venv', '--extend-exclude=.nox')


@nox.session(python='3.12')
def lint(session):
    session.install('ruff')
    session.run('ruff', 'check')


@nox.session(python='3.12')
def mypy(session):
    session.install('.[typing]')
    session.run('mypy', 'djmanhwabookmarks')
    session.run('mypy', 'tasks.py')
