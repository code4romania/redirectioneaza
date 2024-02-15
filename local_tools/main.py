import csv
import logging
import os
import time
from pathlib import Path
from typing import Any, List

from google.cloud import datastore
from google.cloud.datastore import Client as DsClient, Entity, Query

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ROOT = Path(__file__).resolve().parent
CREDENTIALS_PATH = Path(os.path.join(ROOT, "redirectioneaza-87ec85963232.json"))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIALS_PATH)

KINDS = {
    "ngo_entity": {
        "name": "NgoEntity",
        "order": "-date_created",
        "limit": 200,
        "iterations": 2,
        "webapp_to_django": {
            "key.name": "slug",
            "special_status": "has_special_status",
            "description": "description",
            "name": "name",
            "account": "bank_account",
            "cif": "registration_number",
            "address": "address",
            "county": "county",
            "active_region": "active_region",
            "tel": "phone",
            "website": "website",
            "email.lower()": "email",
            "verified": "is_verified",
            "date_created.timestamp()": "date_created",
            "active": "is_active",
            "logo": "logo_url",
            "accepts_forms": "is_accepting_forms",
        },
    },
    "donor": {
        "name": "Donor",
        "order": "-date_created",
        "limit": 200,
        "iterations": 2,
        "webapp_to_django": {
            "anonymous": "is_anonymous",
            "city": "city",
            "county": "county",
            "date_created.timestamp()": "date_created",
            "email.lower()": "email",
            "filename": "filename",
            "first_name": "first_name",
            "geoip": "geoip",
            "has_signed": "has_signed",
            "income": "income_type",
            "last_name": "last_name",
            "ngo.name": "ngo_slug",
            "pdf_url": "pdf_url",
            "tel": "phone",
            "two_years": "two_years",
        },
    },
    "user": {
        "name": "User",
        "order": "-created",
        "limit": 400,
        "iterations": 2,
        "webapp_to_django": {
            "password": "old_password",
            # "auth_ids": "",
            "verified": "is_verified",
            "first_name": "last_name",
            "last_name": "first_name",
            "ngo.name": "ngo_slug",
            "updated.timestamp()": "date_updated",
            "created.timestamp()": "date_created",
            "email.lower()": "email",
        },
    },
    # "job": {
    #     "name": "Job",
    #     "order": "-date_created",
    #     "limit": 50,
    #     "iterations": -1,
    #     "webapp_to_django": {
    #         "ngo": "ngo_id",
    #         "status": "status",
    #         "date_created.timestamp()": "date_created",
    #         "url": "url",
    #         "owner": "owner_id",
    #     },
    # },
}


def write_query_data_to_csv(csv_name, current_kind, items):
    with open(csv_name, "a") as f:
        writer = csv.writer(f)

        for item in items:
            new_row: List[Any] = []
            for composed_parameter in current_kind["webapp_to_django"].keys():
                split_parameters = composed_parameter.split(".")

                try:
                    value = item[split_parameters[0]]
                except KeyError:
                    value = getattr(item, split_parameters[0])

                if value is None:
                    new_row.append("")
                    continue

                for parameter in split_parameters[1:]:
                    if parameter.endswith("()"):
                        parameter = parameter[:-2]
                        value = getattr(value, parameter)()
                    else:
                        value = getattr(value, parameter)

                new_row.append(value)

            writer.writerow(new_row)

    logger.info(f"–– Added the items to {csv_name}")


def query_for_kind(kind_data, limit, offset) -> List[Entity]:
    dts_client: DsClient = datastore.Client()

    start = time.time()

    query: Query = dts_client.query(kind=kind_data["name"])
    query.order = [kind_data["order"]]

    items: List[Entity] = list(query.fetch(limit=limit, offset=offset))

    end = time.time()
    result = end - start

    logger.info(f"–– Retrieved {len(items)} items in {result} seconds.")

    return items


def retrieve_data(csv_name, kind_data):
    limit: int = kind_data["limit"]
    offset: int = 0
    iterations: int = kind_data["iterations"]

    logger.info(f"Retrieving data for {kind_data['name']} a batch of {limit} for {iterations} iterations.")

    runs = 0
    num_items = 0
    while iterations < 0 or runs < iterations:
        logger.info(f"Run #{runs + 1} " + "—" * 40 + "]")

        items = query_for_kind(kind_data, limit, offset)
        num_items += len(items)

        write_query_data_to_csv(csv_name, kind_data, items)

        if len(items) < limit:
            logger.info(f"–– Retrieved {num_items} items of type {kind_data['name']} after {runs + 1} runs.")
            break

        offset += limit
        runs += 1


def create_kind_csv_file(csv_name, current_kind):
    with open(csv_name, "w") as f:
        writer = csv.writer(f)
        writer.writerow(current_kind["webapp_to_django"].values())

    logger.info(f"Created {csv_name}")


def main():
    enabled_kinds = [
        # "ngo_entity",
        # "donor",
        "user",
    ]

    start = time.time()

    for kind_name, kind_data in KINDS.items():
        if kind_name not in enabled_kinds:
            continue

        logger.info(f"Processing {kind_name} " + "=" * 40 + "]")

        csv_name = f"{kind_name}.csv"

        create_kind_csv_file(csv_name, kind_data)

        retrieve_data(csv_name, kind_data)

    end = time.time()

    result = end - start

    logger.info(f"Done in {result} seconds")


if __name__ == "__main__":
    main()
