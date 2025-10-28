import os
from datetime import datetime
from typing import Any, Dict
from xml.etree.ElementTree import Element, ElementTree
from zipfile import ZipFile

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from localflavor.ro.forms import ROCNPField

from donations.models.donors import Donor
from donations.models.ngos import Cause
from donations.views.download_donations.common import (
    XMLNS_DETAILS,
    build_borderou_data,
    build_btn_doc,
    build_donor,
    build_id_doc_from_raw,
    build_imp,
    new_xml_element,
)

# Repurposed from localflavor.ro.forms.ROCNPField
CNP_FIELD = ROCNPField()


def _redirection_has_duplicate_cnp(redirection: Donor, cnp_idx: Dict[str, Dict[str, Any]]) -> bool:
    cnp = redirection.get_cnp()

    try:
        CNP_FIELD.clean(cnp)
    except ValidationError:
        return False

    if cnp in cnp_idx and cnp_idx[cnp]["has_duplicate"]:
        if not cnp_idx[cnp].get("skip", False):
            cnp_idx[cnp]["skip"] = True
        else:
            return True

    return False


def add_xml_to_zip(
    cause: Cause,
    donations_batch: QuerySet[Donor],
    batch_count: int,
    xml_name: str,
    cnp_idx: Dict[str, Dict[str, Any]],
    zip_timestamp: datetime,
    zip_archive: ZipFile,
    zip_64_flag: bool,
):
    xml_element_tree: ElementTree = build_xml(
        xml_index=batch_count,
        cause=cause,
        redirections=donations_batch,
        cnp_idx=cnp_idx,
        timestamp=zip_timestamp,
    )

    with zip_archive.open(os.path.join("xml", xml_name), mode="w", force_zip64=zip_64_flag) as handler:
        xml_element_tree.write(handler, encoding="utf-8", xml_declaration=True, method="xml")


def build_xml(
    xml_index: int,
    cause: Cause,
    redirections: QuerySet[Donor],
    cnp_idx: Dict[str, Dict[str, Any]],
    timestamp: datetime,
) -> ElementTree:
    xml = Element("form1")

    xml.append(build_btn_doc())
    xml.append(Element("semnatura", XMLNS_DETAILS))
    xml.append(Element("Title", XMLNS_DETAILS))
    xml.append(build_id_doc_from_raw(cause.ngo.registration_number, timestamp))
    xml.append(build_imp())

    xml.append(new_xml_element(tag="z_tipPersoana", text="Rad2"))
    xml.append(new_xml_element(tag="z_denEntitate", text=cause.ngo.name, clean="alnums"))
    xml.append(new_xml_element(tag="z_cifEntitate", text=cause.ngo.registration_number, clean="numbers"))
    xml.append(new_xml_element(tag="z_ibanEntitate", text=cause.bank_account, clean="alnum"))

    xml.append(build_borderou_data(xml_index, timestamp, cause))

    for index, redirection in enumerate(redirections):
        if _redirection_has_duplicate_cnp(redirection, cnp_idx):
            continue

        xml.append(build_donor(index, redirection))

    return ElementTree(xml)
