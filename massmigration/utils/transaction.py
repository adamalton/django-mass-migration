# Third party
from django.conf import settings
from django.db import router, transaction as django_transaction
from gcloudc.db import transaction as datastore_transaction

# Mass Migration
from massmigration.models import MigrationRecord


# TODO: if we want to add true multi-database support (i.e. allow migrations on two different
# databases within the same project) then we should probably add a `connection_name` attribute to
# the Migration class and pass that into both here and into .using() calls in various places.
# That said, should you be allowed to run the same migration on two different databases?


def get_transaction(db_alias):
    engine = settings.DATABASES[db_alias]["ENGINE"]
    if engine == "gcloudc.db.backends.datastore":
        return datastore_transaction
    return django_transaction
