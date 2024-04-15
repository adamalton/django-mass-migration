# Third party
from django.conf import settings
from django.db import router, transaction as django_transaction

# Mass Migration
from massmigration.models import MigrationRecord


# TODO: if we want to add true multi-database support (i.e. allow migrations on two different
# databases within the same project) then we should probably add a `connection_name` attribute to
# the Migration class and pass that into both here and into .using() calls in various places.
# That said, should you be allowed to run the same migration on two different databases?


def get_transaction(db_alias):
    engine = settings.DATABASES[db_alias]["ENGINE"]
    transaction = django_transaction
    if engine.startswith("gcloudc.db.backends"):
        try:
            from gcloudc.db import transaction as gcloudc_transaction
            transaction = gcloudc_transaction
        except ImportError:
            # Newer versions of gcloudc use Django transactions.
            pass
    return transaction
