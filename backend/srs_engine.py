from datetime import date, timedelta
from config.settings import MIN_EASINESS

def update_card(card: dict, quality: int) -> dict:
    """
    Applies SM-2 algorithm to update card state.

    Args:
        card    : current card state {interval, easiness, repetitions}
        quality : student rating (0=Again, 2=Hard, 4=Good, 5=Easy)

    Returns:
        dict : updated card state with next_review date
    """

    interval    = card["interval"]
    easiness    = card["easiness"]
    repetitions = card["repetitions"]

    # SM-2 logic
    if quality < 3:
        repetitions = 0
        interval    = 1
    else:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 3
        else:
            interval = round(interval * easiness)
        repetitions += 1

    # Update easiness factor
    easiness = easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    easiness = max(MIN_EASINESS, easiness)

    # Calculate next review date
    next_review = date.today() + timedelta(days=interval)

    return {
        "interval"   : interval,
        "easiness"   : round(easiness, 2),
        "repetitions": repetitions,
        "next_review": next_review.strftime("%Y-%m-%d")
    }