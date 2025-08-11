import os
import sys
from pathlib import Path

def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest file
    after command line options have been parsed.
    """
    # Set a dummy secret key for the tests to run
    os.environ['API_SECRET_KEY'] = 'test_secret_key_for_jules'
    os.environ['ALGORITHM'] = 'HS256'
    os.environ['ACCESS_TOKEN_EXPIRE_MINUTES'] = '30'

    # The 'app' directory should be automatically added to the path by pytest
    # because of the `packages` configuration in pyproject.toml and the fact
    # that we run pytest from the root.
    pass
