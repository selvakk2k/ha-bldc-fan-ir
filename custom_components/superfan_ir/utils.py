from .const import (
    MODEL_ACTIVA,
    MODEL_ATOMBERG,
    MODEL_GOLDMEDAL,
    MODEL_ORIENT,
)

try:
    from infrared_protocols.commands import Command  # type: ignore[import-not-found, import-untyped]
except ImportError:
    class Command:  # type: ignore[no-redef]
        """Fallback Command class when infrared_protocols is not installed."""
        def __init__(self, modulation: int = 38000) -> None:
            self.modulation = modulation

class RawIRCommand(Command):  # type: ignore[misc, valid-type]
    """A raw IR command that takes a list of durations (in microseconds)."""
    
    def __init__(self, raw_timings: list[int], modulation: int = 38000) -> None:
        """Initialize the Raw IR command with alternating positive and negative durations."""
        super().__init__(modulation=modulation)
        self._raw_timings = []
        for i, t in enumerate(raw_timings):
            if i % 2 == 0:
                self._raw_timings.append(t)  # Pulse (high)
            else:
                self._raw_timings.append(-t) # Space (low)

    def get_raw_timings(self) -> list[int]:
        """Get raw timings for the command."""
        return self._raw_timings


def get_manufacturer(model: str) -> str:
    """Return the manufacturer / brand name for a given fan model."""
    if model == MODEL_ATOMBERG:
        return "Atomberg"
    if model == MODEL_ACTIVA:
        return "Activa Appliances"
    if model == MODEL_ORIENT:
        return "Orient Electric"
    if model == MODEL_GOLDMEDAL:
        return "Goldmedal Electricals"
    return "Versa Drives (Superfan)"
