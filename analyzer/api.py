import json

import falcon

import analysis
try:
    import database
    import util
except ModuleNotFoundError:
    print('common package not in python path')


logger = util.Logger(__name__)


class Winrate:
    def on_get(self, req, resp):
        logger.info('/GET winrate')
        params = req.params
        conn = database.get_connection()
        summoner = database.select_summoner(conn=conn,
                                            summoner_name=params['summoner'],
                                            )
        wr = analysis.get_winrate(summoner=summoner,
                                  conn=conn,
                                  )
        resp.body = json.dumps(wr)


def create():
    api = falcon.API()
    api.add_route('/winrate', Winrate())
    logger.info('falcon initialized')

    conn = database.get_connection()
    database.kill_connection(conn)
    logger.info('database is ready')

    return api


application = create()
