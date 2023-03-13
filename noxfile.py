import nox

@nox.session
def tests(session):
    session.run(*"rm -f poetry.lock".split(), external=True)
    session.run(*"poetry export -f requirements.txt --with test --without-hashes --output requirements.txt".split(), external=True)
    session.install(*"-r requirements.txt".split())
    session.install(*". --no-deps".split())

    session.run('pytest')
    session.run(*"rm requirements.txt".split(), external=True)
