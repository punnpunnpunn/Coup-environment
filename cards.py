from enum import Enum


class Role(str, Enum):
    DUKE = "duke"
    ASSASSIN = "assassin"
    CAPTAIN = "captain"
    AMBASSADOR = "ambassador"
    CONTESSA = "contessa"


ALL_ROLES = [
    Role.DUKE,
    Role.ASSASSIN,
    Role.CAPTAIN,
    Role.AMBASSADOR,
    Role.CONTESSA,
]


class Card:
    def __init__(self, role: Role):
        self.role = role
        self.revealed = False

    def __repr__(self) -> str:
        status = "revealed" if self.revealed else "hidden"
        return f"Card({self.role.value}, {status})"
