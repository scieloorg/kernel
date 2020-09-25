import sys
import argparse
import logging
import pkg_resources

from documentstore import adapters


LOGGER = logging.getLogger(__name__)

EPILOG = """\
Copyright 2019 SciELO <scielo-dev@googlegroups.com>.
Licensed under the terms of the BSD license. Please see LICENSE in the source
code for more information.
"""

VERSION = pkg_resources.get_distribution("scielo-kernel").version

LOGGER_FMT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def _create_indexes(args):
    mongo = adapters.MongoDB(args.dsn, args.dbname)
    mongo.create_indexes()


def _create_collections(args):
    mongo = adapters.MongoDB(args.dsn, args.dbname)
    mongo.create_collections()


def cli(argv=None):
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(
        description="SciELO Kernel command line utility.", epilog=EPILOG
    )
    parser.add_argument("-v", "--version", action="version", version=VERSION)
    parser.add_argument("--loglevel", default="")
    subparsers = parser.add_subparsers()

    parser_create_indexes = subparsers.add_parser(
        "create-indexes",
        help="Create all database indexes",
        description="This operation may cause outages. "
        "If you are using replica sets please read "
        "https://docs.mongodb.com/manual/core/index-creation/#index-operations-replicated-build",
    )
    parser_create_indexes.add_argument(
        "dsn", help="DSN for MongoDB node where indexes will be created."
    )
    parser_create_indexes.add_argument("dbname", help="Database name.")
    parser_create_indexes.set_defaults(func=_create_indexes)

    parser_create_collections = subparsers.add_parser(
        "create-collections",
        help="Create all database collections",
        description="Explicitly creates all database collections. "
        "This is required when using MongoDB < 4.4 with the transactional support enabled.",
    )
    parser_create_collections.add_argument(
        "dsn", help="DSN for MongoDB node where collections will be created."
    )
    parser_create_collections.add_argument("dbname", help="Database name.")
    parser_create_collections.set_defaults(func=_create_collections)

    args = parser.parse_args()
    # todas as mensagens serão omitidas se level > 50
    logging.basicConfig(
        level=getattr(logging, args.loglevel.upper(), 999), format=LOGGER_FMT
    )
    return args.func(args)


def main():
    try:
        sys.exit(cli())
    except KeyboardInterrupt:
        LOGGER.info("Got a Ctrl+C. Terminating the program.")
        # É convencionado no shell que o programa finalizado pelo signal de
        # código N deve retornar o código N + 128.
        sys.exit(130)
    except Exception as exc:
        LOGGER.exception(exc)
        sys.exit("An unexpected error has occurred: %s" % exc)


if __name__ == "__main__":
    main()
