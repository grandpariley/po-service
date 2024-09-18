from asyncio import create_task

from fastapi import FastAPI

import db
import po.main
import pomatch.main
from po.pkg.problem.builder import default_portfolio_optimization_problem_by_weights
from pomatch.main import get_responses
from pomatch.pkg.response import Response

app = FastAPI()

# test value 66ea19e61d477acab327bf2b
async def portfolio_optimization(portfolio_id):
    print('did we start this')
    all_responses = await db.get_surveys()
    all_weights = pomatch.main.get_weights(get_responses(all_responses))
    weights = next((weight for weight in all_weights if weight['portfolio_id'] == portfolio_id))
    po.main.main({
        'arch1': default_portfolio_optimization_problem_by_weights(weights),
    })


@app.post("/api/v1/survey/test")
async def survey(portfolio_id):
    create_task(portfolio_optimization(portfolio_id))
    return {'portfolio_id': portfolio_id}

@app.post("/api/v1/survey")
async def survey(survey_result: Response):
    print('got here')
    portfolio_id = await db.insert_survey(survey_result)
    print('did we save it?')
    create_task(portfolio_optimization(portfolio_id))
    return {'portfolio_id': portfolio_id}


@app.get("/api/v1/portfolio/{portfolio_id}/status")
async def status(portfolio_id: str):
    if await db.portfolio_exists(portfolio_id):
        return {'status': 'READY'}
    return {'status': 'PENDING'}


@app.get("/api/v1/portfolio/{portfolio_id}")
async def portfolio(portfolio_id: str):
    return await db.get_portfolio(portfolio_id)
