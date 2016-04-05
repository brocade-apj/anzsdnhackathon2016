from flask import Blueprint, render_template, flash, request, redirect, url_for
from www.extensions import cache
from srmanager.sr import SR
from www.extensions import mongo

main = Blueprint('main', __name__)


@main.route('/')
@cache.cached(timeout=1000)
def home():
    srm = SR()
    topo = []
    for node in srm.get_topology():
      topo.append(str(node))
    return render_template('index.html', topo=topo)

@main.route('/services')
@cache.cached(timeout=1000)
def services():
    services = mongo.db.services.find()
    return render_template('services.html', services=services)
