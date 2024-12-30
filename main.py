import asyncio
import functools
import os

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
BATCH_TASK_ID = 'batch'
tasks = {}

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
    weights = await get_portfolio_weights(portfolio_id)
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


def task_done_callback(task_id, _):
    tasks.pop(task_id, None)


async def is_ready(task_id):
    return (task_id == BATCH_TASK_ID and await db.arch2_portfolios_exist()) or \
        (task_id == BATCH_TASK_ID and await db.portfolio_exists(task_id))


async def get_status_of_task(task_id):
    if task_id not in tasks.keys():
        raise HTTPException(status_code=404, detail="Item not found")
    if not tasks[task_id].done():
        return {'status': 'PENDING'}
    if await is_ready(task_id):
        return {'status': 'READY'}
    if tasks[task_id].cancelled():
        raise HTTPException(status_code=500, detail="Cancelled task")
    raise HTTPException(status_code=500, detail=str(tasks[task_id].exception()))


@app.post("/api/v1/batch")
async def batch():
    tasks[BATCH_TASK_ID] = asyncio.create_task(arch2(), name=BATCH_TASK_ID)
    tasks[BATCH_TASK_ID].add_done_callback(functools.partial(task_done_callback, BATCH_TASK_ID))
    return {'status': 'PENDING'}


@app.get("/api/v1/batch/status")
async def batch_status():
    return await get_status_of_task(BATCH_TASK_ID)


@app.get("/api/v1/portfolio/{portfolio_id}/status")
async def status(portfolio_id: str):
    return await get_status_of_task(portfolio_id)


@app.post("/api/v1/survey")
async def survey(survey_result: Response):
    portfolio_id = await db.insert_survey(survey_result)
    tasks[portfolio_id] = asyncio.create_task(arch1_sync(portfolio_id), name=portfolio_id)
    tasks[portfolio_id].add_done_callback(functools.partial(task_done_callback, portfolio_id))
    return {'portfolio_id': portfolio_id}


@app.get("/api/v1/portfolio/{portfolio_id}")
async def portfolio(portfolio_id: str):
    matched_portfolio = await get_matched_portfolio(portfolio_id)
    custom_portfolios = await db.get_portfolio(portfolio_id)
    matched_portfolio.pop('_id')
    return custom_portfolios['portfolio'] + [matched_portfolio]
