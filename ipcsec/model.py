from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Case:
    case_id: str
    operation: str = 'ECHO'
    declared_length: int = 4
    offset: int = 0
    flags: int = 0
    payload_hex: str = '70696e67'
    mutation: str = 'normal'
    session_id: str = 'session-01'

    def record(self):
        return asdict(self)
