import asyncio
import os
import threading

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

import db
import po.main
from po.match import match_portfolio
from po.pkg.problem.builder import default_portfolio_optimization_problem_by_weights, \
    default_portfolio_optimization_problem_arch_2
from pomatch.pkg.response import Response, get_responses
from pomatch.pkg.weights import get_weights

load_dotenv()
threads = {}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ["FRONTEND_ORIGINS"].split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def arch2_sync():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(arch2())
    loop.close()


def arch1_sync(portfolio_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(portfolio_optimization(portfolio_id))
    loop.close()


async def arch2():
    await db.clear_arch2_portfolio()
    solutions = await po.main.main({
        'arch2': default_portfolio_optimization_problem_arch_2(),
    })
    await db.insert_arch2_portfolios(solutions['arch2'])


async def get_matched_portfolio(portfolio_id):
    weights = await get_portfolio_weights(portfolio_id)
    solutions = await db.get_arch2_portfolios()
    return match_portfolio(weights, solutions)


async def portfolio_optimization(portfolio_id):
    weights = asyncio.run(get_portfolio_weights(portfolio_id))
    solutions = await po.main.main({
        'arch1': default_portfolio_optimization_problem_by_weights(weights),
    })
    for name in solutions.keys():
        await db.insert_portfolio(portfolio_id, solutions[name])


async def get_portfolio_weights(portfolio_id):
    all_responses = await db.get_surveys()
    all_weights = get_weights(get_responses(all_responses))
    weights = next((weight for weight in all_weights if weight['portfolio_id'] == portfolio_id))
    return weights


@app.post("/api/v1/batch")
async def batch():
    threads['batch'] = threading.Thread(target=arch2_sync, daemon=True)
    threads['batch'].start()
    return {'status': 'PENDING'}


@app.get("/api/v1/batch/status")
async def batch():
    if await db.arch2_portfolios_exist():
        return {'status': 'READY'}
    if 'batch' in threads.keys() and threads['batch'].is_alive():
        return {'status': 'PENDING'}
    return {'status': 'ERROR'}


@app.post("/api/v1/survey")
async def survey(survey_result: Response):
    portfolio_id = await db.insert_survey(survey_result)
    threads[portfolio_id] = threading.Thread(target=arch1_sync, args=(portfolio_id,), daemon=True)
    threads[portfolio_id].start()
    return {'portfolio_id': portfolio_id}


@app.get("/api/v1/portfolio/{portfolio_id}/status")
async def status(portfolio_id: str):
    if portfolio_id not in threads.keys():
        raise HTTPException(status_code=404, detail="Item not found")
    if await db.portfolio_exists(portfolio_id):
        return {'status': 'READY'}
    if threads[portfolio_id].is_alive():
        return {'status': 'PENDING'}
    return {'status': 'ERROR'}


@app.get("/api/v1/portfolio/{portfolio_id}")
async def portfolio(portfolio_id: str):
    matched_portfolio = await get_matched_portfolio(portfolio_id)
    custom_portfolios = await db.get_portfolio(portfolio_id)
    matched_portfolio.pop('_id')
    return custom_portfolios['portfolio'] + [matched_portfolio]
