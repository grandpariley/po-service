from asyncio import run
from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4

import db

app = FastAPI()


class SurveyResult(BaseModel):
    field: str

async def portfolio_optimization(survey_result):
    print('we up and runnin')

@app.post("/api/v1/survey")
def survey(survey_result: SurveyResult):
    db.insert_survey(survey_result)
    portfolio_id = uuid4()
    run(portfolio_optimization(survey_result))
    return {'portfolio_id': portfolio_id}


@app.get("/api/v1/portfolio/{portfolio_id}/status")
async def portfolio(portfolio_id: str):
    if db.portfolio_exists(portfolio_id):
        return {'status': 'READY'}
    return {'status': 'PENDING'}


@app.get("/api/v1/portfolio/{portfolio_id}")
async def portfolio(portfolio_id: str):
    return db.get_portfolio(portfolio_id)['portfolio']
