import csv
import logging
import os
from pathlib import Path
from typing import Any, List

import time
from google.cloud import datastore
from google.cloud.datastore import Client as DsClient, Entity, Query

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ROOT = Path(__file__).resolve().parent
CREDENTIALS_PATH = Path(os.path.join(ROOT, "creds.json"))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIALS_PATH)

KINDS = {
    "ngo_entity": {
        "name": "NgoEntity",
        "order": "-date_created",
        "limit": 200,
        "iterations": -1,
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
        "limit": 10000,
        "iterations": -1,
        "webapp_to_django": {
            "anonymous": "is_anonymous",
            "city": "city",
            "county": "county",
            "date_created.timestamp()": "date_created",
            "email.lower()": "email",
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
        "default_values": {
            "has_signed": False,
            "two_years": False,
            "anonymous": True,
            "geoip": {},
            "income": "wage",
        },
        "hard_stop": {
            "output_field": "date_created.timestamp()",
            "operator": "<=",
            "value": 0,
        },
    },
    "user_w_slug": {
        "name": "User",
        "order": "-created",
        "limit": 400,
        "iterations": -1,
        "webapp_to_django": {
            "password": "old_password",
            "verified": "is_verified",
            "first_name.strip()": "last_name",
            "last_name.strip()": "first_name",
            "ngo.name": "ngo_slug",
            "updated.timestamp()": "date_updated",
            "created.timestamp()": "date_created",
            "email.strip().lower()": "email",
            "key.id": "old_id",
        },
        "filter": {
            "field": "ngo",
            "operator": "is",
        },
    },
    "user_wo_slug": {
        "name": "User",
        "order": "-created",
        "limit": 400,
        "iterations": -1,
        "webapp_to_django": {
            "password": "old_password",
            "verified": "is_verified",
            "first_name.strip()": "last_name",
            "last_name.strip()": "first_name",
            "ngo.name": "ngo_slug",
            "updated.timestamp()": "date_updated",
            "created.timestamp()": "date_created",
            "email.strip().lower()": "email",
            "key.id": "old_id",
        },
        "filter": {
            "field": "ngo",
            "operator": "is_not",
        },
    },
    "job": {
        "name": "Job",
        "order": "-date_created",
        "limit": 400,
        "iterations": -1,
        "webapp_to_django": {
            "date_created.timestamp()": "date_created",
            "ngo.name": "ngo_slug",
            "owner.id": "owner_id",
            "status": "status",
            "url": "url",
        },
    },
}


def write_query_data_to_csv(csv_name, current_kind, items):
    with open(csv_name, "a") as f:
        writer = csv.writer(f)

        for item in items:
            new_row: List[Any] = []
            if current_kind.get("filter"):
                if current_kind["filter"]["operator"] == "is":
                    if item[current_kind["filter"]["field"]] is None:
                        continue
                elif current_kind["filter"]["operator"] == "is_not":
                    if item[current_kind["filter"]["field"]] is not None:
                        continue

            for composed_parameter in current_kind["webapp_to_django"].keys():
                split_parameters = composed_parameter.split(".")

                try:
                    try:
                        value = item[split_parameters[0]]
                    except KeyError:
                        value = getattr(item, split_parameters[0])
                except AttributeError:
                    if "default_values" in current_kind and split_parameters[0] not in current_kind["default_values"]:
                        raise KeyError(
                            f"Key '{split_parameters[0]}' not found in item {item} and no default value provided."
                        )
                    value = current_kind["default_values"][split_parameters[0]]

                if value is None:
                    new_row.append("")
                    continue

                for parameter in split_parameters[1:]:
                    if parameter.endswith("()"):
                        parameter = parameter[:-2]
                        value = getattr(value, parameter)()
                    else:
                        value = getattr(value, parameter)

                if "hard_stop" in current_kind and composed_parameter == current_kind["hard_stop"]["output_field"]:
                    compare_value = current_kind["hard_stop"]["value"]
                    if eval(f"{value} {current_kind['hard_stop']['operator']} {compare_value}"):
                        logger.info(
                            f"Hard stop condition met for {composed_parameter} with comparison:"
                            f"[ {value} {current_kind['hard_stop']['operator']} {compare_value} ]"
                        )
                        return False

                new_row.append(value)

            writer.writerow(new_row)

    logger.info(f"–– Added the items to {csv_name}")

    return True


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

        should_continue = write_query_data_to_csv(csv_name, kind_data, items)

        if not should_continue:
            break

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
        "ngo_entity",
        "user_w_slug",
        "user_wo_slug",
        # "donor",
        # "job",
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
