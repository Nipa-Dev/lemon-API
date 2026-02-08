import random

from fastapi import APIRouter, Query

from lemonapi.data import facts, quotes

router = APIRouter()


@router.get("/lemon/facts/random")
async def random_fact():
    """Return a random lemon fact.

    Returns:
        dict: A dictionary with key `message` containing a random fact.
    """
    data = random.choice(facts.LEMON_FACTS)
    return {"message": data}


@router.get("/lemon/facts/amount")
async def amount(count: int = Query(..., ge=1, le=5)):
    """Return multiple random lemon facts.

    Args:
        count (int): Number of facts to return. Must be between 1 and 5.

    Returns:
        dict: A dictionary with key `message` containing a list of facts.
    """
    return {"message": random.sample(facts.LEMON_FACTS, count)}


@router.get("/lemon/verbs")
async def verbs():
    """Return a random lemon-related verb.

    Returns:
        dict: A dictionary with key `message` containing a verb.
    """
    return {"message": random.choice(facts.LEMON_VERBS)}


@router.get("/lemon/nouns")
async def nouns():
    """Return a random lemon-related noun.

    Returns:
        dict: A dictionary with key `message` containing a noun.
    """
    return {"message": random.choice(facts.LEMON_NOUNS)}


@router.get("/quotes/random")
async def quote() -> dict:
    """Return a random quote.

    Returns:
        dict: A dictionary containing a random quote and its author.
    """
    pick = random.choice(quotes.QUOTES)
    return pick
