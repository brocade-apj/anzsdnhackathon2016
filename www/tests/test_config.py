#! ../env/bin/python
# -*- coding: utf-8 -*-
from www import create_app


class TestConfig:
    def test_dev_config(self):
        """ Tests if the development config loads correctly """

        app = create_app('www.settings.DevConfig')

        assert app.config['DEBUG'] is True
        assert app.config['CACHE_TYPE'] == 'null'

    def test_test_config(self):
        """ Tests if the test config loads correctly """

        app = create_app('www.settings.TestConfig')

        assert app.config['DEBUG'] is True
        assert app.config['CACHE_TYPE'] == 'null'

    def test_prod_config(self):
        """ Tests if the production config loads correctly """

        app = create_app('www.settings.ProdConfig')

        assert app.config['CACHE_TYPE'] == 'simple'
