import os
from asyncio import create_task

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import db
import po.main
from po.pkg.problem.builder import default_portfolio_optimization_problem_by_weights
from pomatch.main import get_responses, get_weights
from pomatch.pkg.response import Response

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ["FRONTEND_ORIGINS"].split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def portfolio_optimization(portfolio_id):
    all_responses = await db.get_surveys()
    all_weights = get_weights(get_responses(all_responses))
    weights = next((weight for weight in all_weights if weight['portfolio_id'] == portfolio_id))
    await po.main.main({
        'arch1': default_portfolio_optimization_problem_by_weights(weights),
    }, portfolio_id)


@app.post("/api/v1/survey/test")
async def survey(portfolio_id):
    create_task(portfolio_optimization(portfolio_id))
    return {'portfolio_id': portfolio_id}


@app.post("/api/v1/survey")
async def survey(survey_result: Response):
    portfolio_id = await db.insert_survey(survey_result)
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
