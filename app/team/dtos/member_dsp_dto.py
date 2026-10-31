from pydantic import ConfigDict, Field

from app.core.dtos import BaseDTO


class BaseMembershipDspDTO(BaseDTO):
    """Core fields for a membership data sharing policy"""

    bpm_shared: bool | None = Field(default=None)
    calories_shared: bool | None = Field(default=None)
    respiratory_rate_shared: bool | None = Field(default=None)
    hrv_shared: bool | None = Field(default=None)
    effort_shared: bool | None = Field(default=None)
    skin_temp_delta_shared: bool | None = Field(default=None)


class SetMembershipDspDTO(BaseMembershipDspDTO):
    """Fields a user can set for their data sharing policy within a team"""

    reset: bool = Field(
        default=False,
        description="If true, will reset the policy to be the default for the team as defined by the data sharing requirements",
    )


class MembershipDspDTO(BaseMembershipDspDTO):
    """Data sharing policy for a specific team member"""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    membership_id: int = Field(description="Membership id associated with the policy")

    bpm_shared: bool | None = Field(default=True)
    calories_shared: bool | None = Field(default=True)
    respiratory_rate_shared: bool | None = Field(default=True)
    hrv_shared: bool | None = Field(default=True)
    effort_shared: bool | None = Field(default=True)
    skin_temp_delta_shared: bool | None = Field(default=True)
