import nox
import pathlib

@nox.session
def debug(session):
    import json

    with (pathlib.Path(__file__).parent / "vars.env").open("r") as f:
        print(json.load(f))


@nox.session
def lock(session):
    session.run(*"rm -f poetry.lock".split(), external=True)
    session.run(*"poetry export -f requirements.txt --with test --without-hashes --output requirements.txt".split(), external=True)

@nox.session
def tests(session):
    session.install(*"-r requirements.txt".split())
    session.install(*". --no-deps".split())


    session.run('pytest', *session.posargs)
