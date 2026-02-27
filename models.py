from dataclasses import dataclass


@dataclass
class Event:
    """Represents an attendance event from a device."""
    card: str
    timestamp: int
    origin_id: int

    def to_dto(self) -> tuple[str, int, int]:
        """Convert to DTO format for ERP upload.
        
        Returns:
            Tuple of (card, timestamp, origin_id)
        """
        return (self.card, self.timestamp, self.origin_id)
