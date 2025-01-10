import asyncio

from dotenv import load_dotenv

import db
import po.main
from po.match import match_portfolio
from po.pkg.log import Log
from po.pkg.problem.builder import default_portfolio_optimization_problem_by_weights, \
    default_portfolio_optimization_problem_arch_2
from pomatch.pkg.response import get_responses
from pomatch.pkg.weights import get_weights

load_dotenv()

BATCH_TASK_ID = 'batch'


def listen(portfolio_id):
    if BATCH_TASK_ID == portfolio_id:
        asyncio.run(arch2())
    else:
        asyncio.run(portfolio_optimization(portfolio_id))


async def get_matched_portfolio(portfolio_id):
    weights = await get_portfolio_weights(portfolio_id)
    solutions = await db.get_arch2_portfolios()
    return match_portfolio(weights, solutions)


async def arch2():
    await db.clear_arch2_portfolio()
    solutions = await po.main.main({
        'arch2': default_portfolio_optimization_problem_arch_2(),
    })
    await db.insert_arch2_portfolios(solutions['arch2'])


async def portfolio_optimization(portfolio_id):
    weights = await get_portfolio_weights(portfolio_id)
    solutions = await po.main.main({
        'arch1': default_portfolio_optimization_problem_by_weights(weights),
    })
    for name in solutions.keys():
        await db.insert_portfolio(portfolio_id, solutions[name])
    await db.insert_portfolio(portfolio_id, get_matched_portfolio(portfolio_id))


async def get_portfolio_weights(portfolio_id):
    all_responses = await db.get_surveys()
    all_weights = get_weights(get_responses(all_responses))
    weights = next((weight for weight in all_weights if weight['portfolio_id'] == portfolio_id))
    return weights


if __name__ == "__main__":
    Log.log("connecting to rabbit....")
    import queue_broker

    Log.log("connected to rabbit!")
    Log.log("registering....")
    queue_broker.register_listener(listen)