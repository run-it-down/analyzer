import falcon

import views
import database
import util


logger = util.Logger(__name__)


def create():
    api = falcon.API()
    api.add_route('/winrate', views.BaseMetrics.WinRate())
    api.add_route('/kda', views.BaseMetrics.KDA())
    api.add_route('/cs', views.BaseMetrics.CreepScore())
    api.add_route('/combinations/champions', views.CombinationMetrics.ChampionCombinations())
    api.add_route('/aggression', views.AggressionMetrics.Aggression())

    logger.info('falcon initialized')

    conn = database.get_connection()
    database.kill_connection(conn)
    logger.info('database is ready')

    return api


application = create()

import waitress
waitress.serve(application, host="localhost", port="2000")
