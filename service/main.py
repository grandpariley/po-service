from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI()


class SurveyResult(BaseModel):
    field: str


@app.post("/api/v1/survey")
async def survey(survey_result: SurveyResult):
    return {'portfolio_id': uuid4()}


@app.get("/api/v1/portfolio/{portfolio_id}/status")
async def portfolio(portfolio_id: str):
    print(portfolio_id)
    return {'status': 'PENDING'}


@app.get("/api/v1/portfolio/{portfolio_id}")
async def portfolio(portfolio_id: str):
    print(portfolio_id)
    return {'TSX': 123}
