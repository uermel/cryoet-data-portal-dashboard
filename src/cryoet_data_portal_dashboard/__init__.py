"""cryoET Data Portal Dashboard package."""
# Configure logging at package import time
import logging

# Suppress logs from GraphQL and related libraries globally
logging.getLogger('gql').setLevel(logging.WARNING)
logging.getLogger('gql.transport').setLevel(logging.WARNING)
logging.getLogger('gql.transport.requests').setLevel(logging.WARNING)
logging.getLogger('gql.dsl').setLevel(logging.WARNING)
logging.getLogger('cryoet_data_portal').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
