from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange, InputRequired


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
    object_id = HiddenField()
    submit = SubmitField("Submit")
