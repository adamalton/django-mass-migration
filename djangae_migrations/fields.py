from django.db import models
from gcloudc.db.models.fields.computed import ComputedFieldMixin


# TODO: make a MR to put this into gcloudc
class ComputedDateTimeField(ComputedFieldMixin, models.DateTimeField):
    pass

