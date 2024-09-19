import os

import motor.motor_asyncio
from dotenv import load_dotenv

from po.pkg.problem.problem import problem_encoder_fn
from pomatch.pkg.response import ResponseJSONEncoder

load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URI"])
portfolio = client.po.get_collection('portfolio')
survey = client.po.get_collection('survey')


async def insert_survey(survey_result):
    new_survey = await survey.insert_one(survey_result.model_dump(by_alias=True, exclude=["id"]))
    return str(new_survey.inserted_id)


async def get_surveys():
    cursor = survey.find(None).allow_disk_use(True)
    results = []
    async for result in cursor:
        results.append(result)
    return results


async def insert_portfolio(portfolio_id, portfolio_result):
    await portfolio.insert_one({
        'portfolio_id': portfolio_id,
        'portfolio': list(map(problem_encoder_fn, portfolio_result))
    })


async def portfolio_exists(portfolio_id):
    return await portfolio.estimated_document_count({'portfolio_id': portfolio_id}) > 0


async def get_portfolio(portfolio_id):
    return await portfolio.find_one({'portfolio_id': portfolio_id})
