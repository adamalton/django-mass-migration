from django.db import models
from gcloudc.db.models.fields.computed import ComputedFieldMixin


# TODO: make a MR to put this into gcloudc
class ComputedDateTimeField(ComputedFieldMixin, models.DateTimeField):
    pass


# TODO: make a MR to make this the defualt ComputedCharField in gcloudc
class ComputedCharField(ComputedFieldMixin, models.CharField):
    pass
