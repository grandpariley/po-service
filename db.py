import os

import motor.motor_asyncio
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder

load_dotenv()

client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGO_URI"])
portfolio = client.po.get_collection('portfolio')
survey = client.po.get_collection('survey')


async def insert_survey(survey_result):
    new_survey = await survey.insert_one(survey_result.model_dump(by_alias=True, exclude=["id"]))
    return jsonable_encoder(new_survey.inserted_id)


async def insert_portfolio(portfolio_id, portfolio_result):
    await portfolio.insert_one({
        'portfolio_id': portfolio_id,
        'portfolio': portfolio_result
    })


def portfolio_exists(portfolio_id):
    return portfolio.estimated_document_count({'portfolio_id': portfolio_id}) > 0

def get_portfolio(portfolio_id):
    return portfolio.find_one({'portfolio_id': portfolio_id})
