import csv
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from django.apps import apps as django_apps
from django.conf import settings
from django.db import IntegrityError
from django.db.models.base import ModelBase
from django.utils.timezone import make_aware

from donations.models.main import Ngo
from .models import ImportJob, ImportModelTypeChoices, ImportStatusChoices

logger = logging.getLogger(__name__)


def parse_imported_date(date_str: str):
    timestamp = float(date_str)
    datetime_obj_with_tz = make_aware(datetime.fromtimestamp(timestamp))

    return datetime_obj_with_tz


def map_county(county: str) -> str:
    county_mapping = {
        "Alba": "Alba",
        "Arad": "Arad",
        "Argeș": "Argeș",
        "Arges": "Argeș",
        "Bacău": "Bacău",
        "Bacau": "Bacău",
        "Bihor": "Bihor",
        "Bistrița-Năsăud": "Bistrița-Năsăud",
        "Bistrita-Nasaud": "Bistrița-Năsăud",
        "Bistrița-Nasaud": "Bistrița-Năsăud",
        "Bistrita-Năsaud": "Bistrița-Năsăud",
        "Bistrita-Nasăud": "Bistrița-Năsăud",
        "Bistrița-Năsaud": "Bistrița-Năsăud",
        "Bistrița-Nasăud": "Bistrița-Năsăud",
        "Bistrita-Năsăud": "Bistrița-Năsăud",
        "Botoșani": "Botoșani",
        "Botosani": "Botoșani",
        "Brașov": "Brașov",
        "Brasov": "Brașov",
        "Brăila": "Brăila",
        "Braila": "Brăila",
        "București": "București",
        "Bucuresti": "București",
        "Buzău": "Buzău",
        "Buzau": "Buzău",
        "Caraș-Severin": "Caraș-Severin",
        "Caras-Severin": "Caraș-Severin",
        "Călărași": "Călărași",
        "Calarasi": "Călărași",
        "Călarasi": "Călărași",
        "Calărasi": "Călărași",
        "Calarași": "Călărași",
        "Călărasi": "Călărași",
        "Călarași": "Călărași",
        "Calărași": "Călărași",
        "Cluj": "Cluj",
        "Constanța": "Constanța",
        "Constanta": "Constanța",
        "Covasna": "Covasna",
        "Dâmbovița": "Dâmbovița",
        "Dambovita": "Dâmbovița",
        "Dâmbovita": "Dâmbovița",
        "Dambovița": "Dâmbovița",
        "Dolj": "Dolj",
        "Galati": "Galați",
        "Giurgiu": "Giurgiu",
        "Gorj": "Gorj",
        "Harghita": "Harghita",
        "Hunedoara": "Hunedoara",
        "Ialomița": "Ialomița",
        "Ialomita": "Ialomița",
        "Iași": "Iași",
        "Iasi": "Iași",
        "Ilfov": "Ilfov",
        "Maramureș": "Maramureș",
        "Maramures": "Maramureș",
        "Mehedinți": "Mehedinți",
        "Mehedinti": "Mehedinți",
        "Mureș": "Mureș",
        "Mures": "Mureș",
        "Neamț": "Neamț",
        "Neamt": "Neamț",
        "Olt": "Olt",
        "Prahova": "Prahova",
        "Satu Mare": "Satu Mare",
        "Sălaj": "Sălaj",
        "Salaj": "Sălaj",
        "Sibiu": "Sibiu",
        "Suceava": "Suceava",
        "Teleorman": "Teleorman",
        "Timiș": "Timiș",
        "Timis": "Timiș",
        "Tulcea": "Tulcea",
        "Vaslui": "Vaslui",
        "Vâlcea": "Vâlcea",
        "Valcea": "Vâlcea",
        "Vrancea": "Vrancea",
    }

    return county_mapping.get(county, county)


def ngo_slugs_to_ids(ngo_slugs: str) -> List[int]:
    ngo_slugs = ngo_slugs.split(",")
    ngo_ids = []

    for slug in ngo_slugs:
        try:
            ngo_ids.append(Ngo.objects.get(slug=slug).id)
        except Ngo.DoesNotExist:
            logger.warning(f"NGO with slug {slug} not found")

    return ngo_ids


IMPORT_DETAILS = {
    # TODO: The old "logo" field should be saved to the new "logo_url" field
    ImportModelTypeChoices.NGO.value: {
        "default_header": (
            "slug,has_special_status,description,name,bank_account,registration_number,address,county,"
            "active_region,phone,website,email,is_verified,date_created,is_active,logo_url,is_accepting_forms"
        ),
        "fields_mapping": {
            "date_created": parse_imported_date,
            "bank_account": lambda x: x.replace(" ", ""),
            "address": lambda x: x.strip(),
            "county": map_county,
            "active_region": map_county,
        },
        "fields_post": {},
    },
    ImportModelTypeChoices.USER.value: {
        "default_header": "old_password,is_verified,last_name,first_name,ngo_slug,date_updated,date_created,email",
        "fields_mapping": {
            "date_created": parse_imported_date,
            "date_updated": parse_imported_date,
        },
        "fields_post": {},
    },
    ImportModelTypeChoices.DONOR.value: {
        "default_header": (
            "is_anonymous,city,county,date_created,email,filename,first_name,"
            "geoip,has_signed,income_type,last_name,ngo_slug,pdf_url,phone,two_years"
        ),
        "fields_mapping": {
            "date_created": parse_imported_date,
            "county": map_county,
        },
        "fields_post": {},
    },
    ImportModelTypeChoices.PARTNER.value: {
        "default_header": "subdomain,name,has_custom_header,has_custom_note,ngo_slugs",
        "fields_mapping": {},
        "fields_post": {
            "identifier": "subdomain",
            "fields": {"ngos": ngo_slugs_to_ids},
        },
    },
    ImportModelTypeChoices.JOB.value: {
        "default_header": "date_created,ngo_slug,owner_id,status,url",
        "fields_mapping": {
            "date_created": parse_imported_date,
        },
        # TODO: create an import branch to allow one-by-one import of ite
        "fields_post": {},
    },
}


def process_import_task(import_id):
    logger.info(f"Processing import {import_id}")

    import_obj = ImportJob.objects.get(id=import_id)
    import_obj.status = ImportStatusChoices.PROCESSING
    import_obj.save()

    try:
        run_import(import_obj)
    except Exception as e:
        import_obj.status = ImportStatusChoices.ERROR
        import_obj.save()

        logger.exception(f"Error processing import {import_id}: {e}")

    return import_obj


def run_import(import_obj: ImportJob):
    raw_data: List[Dict] = extract_data_from_csv(import_obj)

    import_model_name = ImportModelTypeChoices(import_obj.import_type).value
    import_model = django_apps.get_model(import_model_name)

    import_data = process_raw_data(import_obj, import_model, raw_data)

    logger.info(
        f"Importing {len(import_data['processed_data'])} rows into {import_model_name} "
        f"with a batch size of {settings.IMPORT_BATCH_SIZE}"
    )

    import_data_into_db(import_obj, import_data, import_model)

    import_obj.status = ImportStatusChoices.DONE
    import_obj.save()


def import_data_into_db(import_obj: ImportJob, import_data: Dict[str, Union[List[Dict], Dict]], import_model):
    batch_number = 0
    items_imported = 0

    post_import_details = IMPORT_DETAILS[import_obj.import_type]["fields_post"]
    post_data_identifier = post_import_details.get("identifier", None)

    existing_items: List[Any] = []
    if post_data := import_data.get("post_data"):
        existing_items = list(import_model.objects.all().values_list(post_data_identifier, flat=True))

    processed_data = import_data["processed_data"]

    for i in range(0, len(processed_data), settings.IMPORT_BATCH_SIZE):
        import_batch = processed_data[i : i + settings.IMPORT_BATCH_SIZE]
        try:
            batch_ = [import_model(**item) for item in import_batch]
            import_model.objects.bulk_create(batch_)

            items_imported += len(import_batch)
            logger.info(f"Batch {batch_number} imported")
        except IntegrityError:
            logger.warning(f"Error importing batch {batch_number}:, retrying with single items")

            for item in import_batch:
                try:
                    items_imported += 1

                    import_model.objects.create(**item)
                except IntegrityError as e:
                    logger.exception(f"Error importing item #{items_imported + 1} {item}: {e}")
                except Exception as e:
                    logger.exception(f"Error importing item #{items_imported + 1} {item}: {e}")

        batch_number += 1

    if post_data:
        for identifier, data in post_data.items():
            if identifier in existing_items:
                continue
            else:
                obj = import_model.objects.get(**{post_data_identifier: identifier})

            for field, value in data.items():
                field_processor: Optional[callable] = post_import_details["fields"][field]

                if field_processor:
                    value = field_processor(value)

                getattr(obj, field).add(*value)

            obj.save()

    logger.info(f"Imported {items_imported} items into {import_model}")


def process_raw_data(
    import_obj: ImportJob, import_model: ModelBase, raw_data: List[Dict]
) -> Dict[str, Union[List[Dict], Dict]]:
    logger.info(
        f"Importing {len(raw_data)} rows into {import_model} " f"with a batch size of {settings.IMPORT_BATCH_SIZE}"
    )

    field_details = IMPORT_DETAILS[import_obj.import_type]

    post_data = {}
    post_data_identifier = field_details["fields_post"].get("identifier", None)

    processed_data: List[Dict] = []
    for index, raw_item in enumerate(raw_data):
        item = {}
        for field, value in raw_item.items():
            if field in field_details.get("fields_post", {}).get("fields", {}).keys():
                post_data[item[post_data_identifier]] = {field: value}
                continue
            elif field in field_details["fields_mapping"]:
                value = field_details["fields_mapping"][field](value)
            elif field == "ngo_slug":
                if not value:
                    continue

                try:
                    ngo_id = Ngo.objects.get(slug=value).id
                except Ngo.DoesNotExist:
                    logger.warning(f"NGO with slug {value} not found at row {index + 1}")
                    continue

                item["ngo_id"] = ngo_id
                continue

            item[field] = value

        processed_data.append(item)

    return {"processed_data": processed_data, "post_data": post_data}


def extract_data_from_csv(import_obj) -> List[Dict]:
    import_data: List[Dict] = []
    with open(import_obj.csv_file.path, "r") as f:
        reader = csv.reader(f)
        if import_obj.has_header:
            header = next(reader)
        else:
            default_header = IMPORT_DETAILS[import_obj.import_type]["default_header"]
            header = default_header.split(",")

        for row in reader:
            import_data.append(dict(zip(header, row)))

    logger.info(f"Extracted {len(import_data)} rows from {import_obj.csv_file.path}")

    return import_data
