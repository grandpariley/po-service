import asyncio
import os
import threading
from asyncio import create_task

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

import db
import po.main
from po.pkg.problem.builder import default_portfolio_optimization_problem_by_weights
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

def portfolio_optimization(portfolio_id):
    all_responses = asyncio.run(db.get_surveys())
    all_weights = get_weights(get_responses(all_responses))
    weights = next((weight for weight in all_weights if weight['portfolio_id'] == portfolio_id))
    solutions = asyncio.run(po.main.main({
        'arch1': default_portfolio_optimization_problem_by_weights(weights),
    }, portfolio_id))
    for name in solutions.keys():
        asyncio.run(db.insert_portfolio(portfolio_id, solutions[name]))


@app.post("/api/v1/survey")
async def survey(survey_result: Response):
    portfolio_id = await db.insert_survey(survey_result)
    threads[portfolio_id] = threading.Thread(target=portfolio_optimization, args=(portfolio_id,), daemon=True)
    threads[portfolio_id].start()
    return {'portfolio_id': portfolio_id}


@app.get("/api/v1/portfolio/{portfolio_id}/status")
async def status(portfolio_id: str):
    if portfolio_id not in threads.keys():
        raise HTTPException(status_code=404, detail="Item not found")
    print(portfolio_id + " is alive: " + str(threads[portfolio_id].is_alive()))
    if await db.portfolio_exists(portfolio_id):
        return {'status': 'READY'}
    if threads[portfolio_id].is_alive():
        return {'status': 'PENDING'}
    return {'status': 'ERROR'}


@app.get("/api/v1/portfolio/{portfolio_id}")
async def portfolio(portfolio_id: str):
    return await db.get_portfolio(portfolio_id)
