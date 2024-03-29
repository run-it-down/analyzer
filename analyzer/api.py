import falcon

import views
import database
import util


logger = util.Logger(__name__)


def create():
    api = falcon.App(cors_enable=True)
    api.add_route('/common-games', views.BaseMetrics.CommonGames())
    api.add_route('/winrate', views.BaseMetrics.WinRate())
    api.add_route('/kda', views.BaseMetrics.KDA())
    api.add_route('/cs', views.BaseMetrics.CreepScore())
    api.add_route('/combinations/champions', views.CombinationMetrics.ChampionCombinations())
    api.add_route('/aggression', views.AggressionMetrics.Aggression())
    api.add_route('/avg-role', views.BaseMetrics.AverageRole())
    api.add_route('/gold-diff', views.BaseMetrics.GoldDifference())
    api.add_route('/avg-game', views.BaseMetrics.AverageGame())

    api.add_route('/classification/millionaire', views.Classification.Millionaire())
    api.add_route('/classification/match-type', views.Classification.MatchType())
    api.add_route('/classification/murderous-duo', views.Classification.MurderousDuo())
    api.add_route('/classification/duo-type', views.Classification.DuoType())
    api.add_route('/classification/farmer-type', views.Classification.FarmerType())
    api.add_route('/classification/tactician', views.Classification.Tactician())

    api.add_route('/average/aggression', views.Averages.AverageAggression())
    api.add_route('/average/basics', views.Averages.AverageBasics())
    api.add_route('/average/win-rate', views.Averages.AverageWinRate())
    api.add_route('/average/cs', views.Averages.AverageCs())

    api.add_route('/model/millionaire', views.ClassificationModel.MillionaireModel())
    api.add_route('/model/murderous-duo', views.ClassificationModel.MurderousDuoModel())
    api.add_route('/model/farmer-type', views.ClassificationModel.FarmerType())
    api.add_route('/model/tactician', views.ClassificationModel.TacticianModel())

    logger.info('falcon initialized')

    conn = database.get_connection()
    database.kill_connection(conn)
    logger.info('database is ready')

    return api


application = create()
