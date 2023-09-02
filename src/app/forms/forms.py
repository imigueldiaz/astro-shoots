from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    FloatField,
    IntegerField,
    SubmitField,
    HiddenField,
    DateField,
)
from wtforms.validators import DataRequired, NumberRange, InputRequired, Optional


class ObjectForm(FlaskForm):
    object_name = StringField("Object Name", validators=[DataRequired()])
    latitude = FloatField(
        "Latitude", validators=[InputRequired(), NumberRange(-90, 90)]
    )
    longitude = FloatField(
        "Longitude", validators=[InputRequired(), NumberRange(-180, 180)]
    )
    sensor_height_mm = FloatField(
        "Sensor Height (mm)", validators=[DataRequired(), NumberRange(1, 100)]
    )
    sensor_width_mm = FloatField(
        "Sensor Width (mm)", validators=[DataRequired(), NumberRange(1, 100)]
    )
    focal_length = FloatField(
        "Focal Length", validators=[DataRequired(), NumberRange(1, 10000)]
    )
    shoot_interval = FloatField(
        "Shoot Interval", validators=[InputRequired(), NumberRange(0, 999)]
    )
    aperture = FloatField(
        "Aperture", validators=[InputRequired(), NumberRange(0.8, 64)]
    )
    number_of_pixels_in_width = IntegerField(
        "Width px", validators=[DataRequired(), NumberRange(1, 9999)]
    )
    number_of_pixels_in_height = IntegerField(
        "Height px", validators=[DataRequired(), NumberRange(1, 9999)]
    )

    camera_position = IntegerField(
        "Camera Position", validators=[InputRequired(), NumberRange(-90, 90)]
    )

    observation_date = DateField(
        "Observation Date", validators=[DataRequired()], format="%Y-%m-%d"
    )
    min_degrees = IntegerField(
        "Minimum Degrees (over the horizon)",
        validators=[InputRequired(), NumberRange(0, 90)],
        default=5,
    )
    altitude = IntegerField("Altitude", validators=[Optional(), NumberRange(0, 9999)])
    object_id = HiddenField()
    camera = StringField("Select Camera", validators=[Optional()])

    submit = SubmitField("Submit")
