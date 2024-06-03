# Third party
from django.conf import settings
from django.db import transaction as django_transaction


def get_transaction(db_alias):
    engine = settings.DATABASES[db_alias]["ENGINE"]
    transaction = django_transaction
    if engine == "gcloudc.db.backends.datastore":
        try:
            from gcloudc.db import transaction as gcloudc_transaction
            transaction = gcloudc_transaction
        except ImportError:
            # Newer versions of gcloudc use Django transactions.
            pass
    return transaction
