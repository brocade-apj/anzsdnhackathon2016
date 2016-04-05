from flask import Blueprint, render_template, flash, request, redirect, url_for
from www.extensions import cache
from srmanager.sr import SR

main = Blueprint('main', __name__)


@main.route('/')
@cache.cached(timeout=1000)
def home():
    srm = SR()
    return render_template('index.html', topo=srm.get_topology())

@main.route('/services')
@cache.cached(timeout=1000)
def services():
    return render_template('services.html')
