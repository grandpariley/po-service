import os

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.environ['MONGO_URI'])
portfolio = client['po']['portfolio']
survey = client['po']['survey']


def insert_survey(survey_result):
    survey.insert_one(survey_result)


def insert_portfolio(portfolio_id, portfolio_result):
    portfolio.insert_one({
        'portfolio_id': portfolio_id,
        'portfolio': portfolio_result
    })


def portfolio_exists(portfolio_id):
    return portfolio.estimated_document_count({'portfolio_id': portfolio_id}) > 0

def get_portfolio(portfolio_id):
    return portfolio.find_one({'portfolio_id': portfolio_id})
