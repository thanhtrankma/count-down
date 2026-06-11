import re
import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import MAX_DURATION_SECONDS
from app.utils.counter_label import validate_countup_range
from app.utils.time_format import parse_time

TIME_REGEX = re.compile(r"^(\d{2}):(\d{2}):(\d{2})$")
RESOLUTION_REGEX = re.compile(r"^(\d{3,5})x(\d{3,5})$")


class CounterMode(str, Enum):
    COUNTDOWN = "countdown"
    COUNTUP = "countup"


class CountdownAnimation(str, Enum):
    NONE = "none"
    FADE = "fade"
    SCALE = "scale"
    SLIDE_UP = "slide_up"
    FLIP = "flip"
    CIRCLE = "circle"


class RenderStyle(BaseModel):
    font_name: str = "Arial"
    font_id: Optional[str] = Field(
        default=None,
        description="Custom font id from fonts.json manifest",
    )
    font_size: int = Field(default=120, ge=8, le=500)
    color: str = "#FFFFFF"
    title_font_size: int = Field(default=48, ge=8, le=300)
    animation: CountdownAnimation = CountdownAnimation.NONE
    animation_intensity: float = Field(default=1.0, ge=0.5, le=1.5)

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise ValueError("color must be a hex value like #RRGGBB")
        return value.upper()


class RenderConfig(BaseModel):
    start_time: str = Field(description="Counter label at t=0 in HH:MM:SS")
    counter_mode: CounterMode = CounterMode.COUNTDOWN
    duration_seconds: int = Field(ge=1, le=MAX_DURATION_SECONDS)
    resolution: str = "1920x1080"
    background_color: str = "#000000"
    style: RenderStyle = Field(default_factory=RenderStyle)
    title: Optional[str] = None
    audio_tick: bool = Field(
        default=False,
        description="Play a short tick sound at each second boundary",
    )

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, value: str) -> str:
        match = TIME_REGEX.match(value)
        if not match:
            raise ValueError("start_time must match HH:MM:SS")
        _, minutes, seconds = match.groups()
        if int(minutes) >= 60 or int(seconds) >= 60:
            raise ValueError("start_time has invalid minute or second values")
        return value

    @field_validator("background_color")
    @classmethod
    def validate_background_color(cls, value: str) -> str:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
            raise ValueError("background_color must be a hex value like #RRGGBB")
        return value.upper()

    @field_validator("resolution")
    @classmethod
    def validate_resolution(cls, value: str) -> str:
        if not RESOLUTION_REGEX.match(value):
            raise ValueError("resolution must be in WIDTHxHEIGHT format")
        return value

    @model_validator(mode="after")
    def validate_counter_mode_range(self) -> "RenderConfig":
        if self.counter_mode == CounterMode.COUNTUP:
            start_seconds = parse_time(self.start_time)
            validate_countup_range(start_seconds, self.duration_seconds)
        return self

    @property
    def width(self) -> int:
        return int(self.resolution.split("x")[0])

    @property
    def height(self) -> int:
        return int(self.resolution.split("x")[1])


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RenderJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    config: RenderConfig
    output_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    error: Optional[str] = None
