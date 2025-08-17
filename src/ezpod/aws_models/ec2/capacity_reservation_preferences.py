from enum import Enum


class CapacityReservationPreferences(str, Enum):
    capacity_reservations_only = "capacity-reservations-only"
    open = "open"
    none = "none"


class CapacityReservationTarget(BaseModel):
    CapacityReservationId: str
    CapacityReservationResourceGroupArn: str


class CapacityReservationPrefs(BaseModel):
    CapacityReservationPreference: CapacityReservationPreferences
    CapacityReservationTarget: CapacityReservationTarget
