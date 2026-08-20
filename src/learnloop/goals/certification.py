"""Single certification threshold shared by every Demonstrated projection."""

DEMONSTRATED_CREDIT = 1.0


def is_demonstrated_credit(credit: float) -> bool:
    return float(credit) >= DEMONSTRATED_CREDIT
