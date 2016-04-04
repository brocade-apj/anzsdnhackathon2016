import pytest

from www import create_app

@pytest.fixture()
def testapp(request):
    app = create_app('www.settings.TestConfig')
    client = app.test_client()
    return client
