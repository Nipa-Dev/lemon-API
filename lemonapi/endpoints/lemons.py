import random

from fastapi import APIRouter, Request

from lemonapi import facts, quotes

router = APIRouter()


@router.get("/lemon/facts/random")
async def random_fact(request: Request):
    """
    Return random fact about lemons from list
    :param request:
    :return: dict with key message that gives access to the data
    """
    data = random.choice(facts.LEMON_FACTS)
    return {"message": data}


@router.get("/lemon/facts/amount")
async def amount(request: Request, count: int = 0):
    """
    Endpoint returns a max 5 facts per time, has no default value.
    :param request:
    :param count: integer that specifies the number of facts given
    :return: dict with key message that gives access to the data
    """
    if count > 5:
        return {"message": "Max allowed number is 5"}
    elif count > 0 and count <= 5:
        return {"message": random.sample(facts.LEMON_FACTS, count)}
    else:
        return {"message": "An error occurred"}


@router.get("/lemon/verbs")
async def verbs(request: Request):
    """
    Endpoint returns random verb about lemons from list
    :param request:
    :return: dict with key message that gives access to the data
    """
    return {"message": random.choice(facts.LEMON_VERBS)}


@router.get("/lemon/nouns")
async def nouns(request: Request):
    """
    Endpoint returns random noun about lemons from list:

    - **param:** request:
    - **param:** dict with key message that gives access to the data
    - test: param format
    """
    return {"message": random.choice(facts.LEMON_NOUNS)}


@router.get("/quotes/random")
async def quote(request: Request) -> dict:
    """
    Endpoint returns random quote with author, you can access that quote
    with key "message".

    - param: request
    - return: dict with message key that gives access to dict with random
    quote & author.
    """
    pick = random.choice(quotes.QUOTES)
    return {"message": pick}
