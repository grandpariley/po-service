from asyncio import run

from fastapi import FastAPI

import db
from pomatch.pkg.response import Response

app = FastAPI()


async def portfolio_optimization(survey_result):
    print('we up and runnin')


@app.post("/api/v1/survey")
async def survey(survey_result: Response):
    portfolio_id = await db.insert_survey(survey_result)
    # run(portfolio_optimization(survey_result))
    return {'portfolio_id': portfolio_id}


@app.get("/api/v1/portfolio/{portfolio_id}/status")
async def portfolio(portfolio_id: str):
    if await db.portfolio_exists(portfolio_id):
        return {'status': 'READY'}
    return {'status': 'PENDING'}


@app.get("/api/v1/portfolio/{portfolio_id}")
async def portfolio(portfolio_id: str):
    return await db.get_portfolio(portfolio_id)['portfolio']
