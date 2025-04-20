import asyncio

from dotenv import load_dotenv

import db
import po.main
from arch2_main import arch2
from po.match import match_portfolio
from po.pkg.log import Log
from po.pkg.problem.builder import default_portfolio_optimization_problem_by_weights
from pomatch.pkg.response import get_responses
from pomatch.pkg.weights import get_weights

load_dotenv()

BATCH_TASK_ID = 'batch'
HEALTH_CHECK_ID = 'health_check'

def listen(portfolio_id):
    if HEALTH_CHECK_ID == portfolio_id:
        Log.log("healthy!")
    elif BATCH_TASK_ID == portfolio_id:
        asyncio.run(arch2())
    else:
        asyncio.run(portfolio_optimization(portfolio_id))


async def get_matched_portfolio(portfolio_id):
    weights = await get_portfolio_weights(portfolio_id)
    solutions = await db.get_arch2_portfolios()
    return match_portfolio(weights, solutions)


async def portfolio_optimization(portfolio_id):
    try:
        await db.insert_queue_started(portfolio_id)
        weights = await get_portfolio_weights(portfolio_id)
        solutions = await po.main.main({
            'arch1': default_portfolio_optimization_problem_by_weights(weights),
        })
        for name in solutions.keys():
            await db.insert_portfolio(portfolio_id, solutions[name])
        await db.insert_portfolio(portfolio_id, get_matched_portfolio(portfolio_id))
        await db.insert_queue_complete(portfolio_id)
    except Exception as e:
        await db.insert_queue_error(portfolio_id, e)


async def get_portfolio_weights(portfolio_id):
    all_responses = await db.get_surveys()
    all_weights = get_weights(get_responses(all_responses))
    weights = get_weights_by_portfolio_id(all_weights, portfolio_id)
    return weights


def get_weights_by_portfolio_id(all_weights, portfolio_id):
    return [weight for weight in all_weights if weight['portfolio_id'] == portfolio_id][0]

arch2()

Log.log("connecting to rabbit....")
import queue_broker

Log.log("connected to rabbit!")
Log.log("registering....")
queue_broker.register_listener(listen)