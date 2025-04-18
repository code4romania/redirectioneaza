import os
from datetime import datetime
from typing import Any, Dict
from xml.etree.ElementTree import Element, ElementTree
from zipfile import ZipFile

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from localflavor.ro.forms import ROCNPField

from donations.common.validation.phone_number import clean_phone_number
from donations.models.donors import Donor
from donations.models.ngos import Cause, Ngo
from redirectioneaza.common.clean import (
    clean_text_alnum,
    clean_text_alphabet,
    clean_text_custom,
    clean_text_email,
    clean_text_numbers,
    duration_flag_to_int,
    unicode_to_ascii,
)

XMLNS_DETAILS = {"xmlns:xfa": "http://www.xfa.org/schema/xfa-data/1.0/", "xfa:dataNode": "dataGroup"}
ANAF_FORM_VERSION = "B230_A1.0.9"

CLEAN_TEXT_CHOICES = {
    "alphabet": lambda text: clean_text_alphabet(text),
    "alphabets": lambda text: clean_text_alphabet(text, allow_spaces=True),
    "alnum": lambda text: clean_text_alnum(text),
    "alnums": lambda text: clean_text_alnum(text, allow_spaces=True),
    "numbers": lambda text: clean_text_numbers(text),
    "email": lambda text: clean_text_email(text),
    "custom": lambda text: clean_text_custom(text),
}

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


def _new_element(tag: str, text: str = None, clean: str = "") -> Element:
    element = Element(tag)

    if text:
        # ANAF has a limit of 75 to 250 characters for each field
        text = text[:250]

        if clean:
            text = unicode_to_ascii(text.strip())
            text = CLEAN_TEXT_CHOICES.get(clean)(text)
            text = " ".join(text.split())
            text = text.upper()

        element.text = text

    return element


def build_xml(
    xml_index: int,
    cause: Cause,
    redirections: QuerySet[Donor],
    cnp_idx: Dict[str, Dict[str, Any]],
    timestamp: datetime,
) -> ElementTree:
    xml = Element("form1")

    xml.append(_build_btn_doc())
    xml.append(Element("semnatura", XMLNS_DETAILS))
    xml.append(Element("Title", XMLNS_DETAILS))
    xml.append(_build_id_doc(cause.ngo, timestamp))
    xml.append(_build_imp())

    xml.append(_new_element(tag="z_tipPersoana", text="Rad2"))
    xml.append(_new_element(tag="z_denEntitate", text=cause.ngo.name, clean="alnums"))
    xml.append(_new_element(tag="z_cifEntitate", text=cause.ngo.registration_number, clean="numbers"))
    xml.append(_new_element(tag="z_ibanEntitate", text=cause.bank_account, clean="alnum"))

    xml.append(_build_borderou_data(xml_index, timestamp, cause))

    for index, redirection in enumerate(redirections):
        if _redirection_has_duplicate_cnp(redirection, cnp_idx):
            continue

        xml.append(_build_donor(index, redirection))

    return ElementTree(xml)


def _build_btn_doc() -> Element:
    element = Element("btnDoc")

    element.append(Element("btnSalt"))
    element.append(Element("btnWebService"))

    info = Element("info")
    info.append(Element("help", XMLNS_DETAILS))

    element.append(info)

    return element


def _build_id_doc(ngo: Ngo, timestamp: datetime) -> Element:
    element = Element("IdDoc")

    element.append(_new_element(tag="universalCode", text=ANAF_FORM_VERSION))

    totalPlata_A = Element("totalPlata_A")
    element.append(totalPlata_A)

    element.append(_new_element(tag="cif", text=ngo.registration_number, clean="numbers"))
    element.append(_new_element(tag="formValid", text="FORMULAR NEVALIDAT"))
    element.append(_new_element(tag="luna_r", text="12"))
    element.append(_new_element(tag="d_rec", text="0"))
    element.append(_new_element(tag="an_r", text=str(timestamp.year - 1)))

    return element


def _build_imp() -> Element:
    element = Element("imp")

    bifaI = Element("bifaI")
    bifaI.append(_new_element(tag="rprI", text="0"))

    element.append(bifaI)

    return element


def _build_borderou_data(xml_index: int, timestamp: datetime, cause: Cause) -> Element:
    element = Element("nrDataB")

    element.append(_new_element(tag="nrD", text=str(xml_index)))
    element.append(_new_element(tag="dataD", text=timestamp.strftime("%d.%m.%Y")))
    element.append(_new_element(tag="denD", text=cause.ngo.name, clean="alnums"))
    element.append(_new_element(tag="cifD", text=cause.ngo.registration_number, clean="numbers"))

    ngo_address: str = cause.ngo.address
    if cause.ngo.locality:
        ngo_address += ", " + cause.ngo.locality
    if cause.ngo.county:
        ngo_address += ", " + cause.ngo.county
    element.append(_new_element(tag="adresaD", text=ngo_address, clean="custom"))

    element.append(_new_element(tag="ibanD", text=cause.bank_account, clean="alnum"))

    return element


def _build_donor(index: int, donor: Donor) -> Element:
    element = Element("contrib")

    nrCrt = Element("nrCrt")
    nrCrt.append(_new_element("nV", str(index + 1)))
    element.append(nrCrt)

    contributor_identity = Element("idCnt")
    contributor_identity.append(_new_element(tag="nume", text=donor.l_name.upper(), clean="alphabets"))
    contributor_identity.append(_new_element(tag="init", text=donor.initial.upper(), clean="alphabet"))
    contributor_identity.append(_new_element(tag="pren", text=donor.f_name.upper(), clean="alphabets"))
    contributor_identity.append(_new_element(tag="cif_c", text=donor.get_cnp(), clean="numbers"))
    contributor_identity.append(
        _new_element(tag="adresa", text=donor.get_address(include_full=True)["full_address"], clean="custom")
    )
    contributor_identity.append(_new_element(tag="telefon", text=clean_phone_number(donor.phone), clean="numbers"))
    contributor_identity.append(_new_element(tag="fax"))
    contributor_identity.append(_new_element(tag="email", text=donor.email, clean="email"))
    element.append(contributor_identity)

    s15 = Element("s15")
    contribution_data = Element("date")
    contribution_data.append(nrCrt)

    contribution_data.append(_build_donor_field_sum_option())
    contribution_data.append(_build_donor_field_bursa())
    contribution_data.append(_build_donor_field_entitate(donor))

    s15.append(contribution_data)
    element.append(s15)

    return element


def _build_donor_field_sum_option():
    optiuneSuma = Element("optiuneSuma")
    slct = Element("slct")
    slct.append(_new_element("ent", text="1"))
    slct.append(_new_element("brs", text="0"))
    optiuneSuma.append(slct)
    return optiuneSuma


def _build_donor_field_bursa():
    brs = Element("brs")

    brs.append(Element("Gap", XMLNS_DETAILS))

    idEnt = Element("idEnt")

    nrDataC = Element("nrDataC")
    nrDataC.append(Element("nrD"))
    nrDataC.append(Element("dataD"))
    idEnt.append(nrDataC)

    nrDataP = Element("nrDataP")
    nrDataP.append(Element("nrD"))
    nrDataP.append(Element("dataD"))
    nrDataP.append(_new_element("venitB"))
    idEnt.append(nrDataP)

    brs.append(idEnt)

    return brs


def _build_donor_field_entitate(donor: Donor):
    ent = Element("ent")

    ent.append(Element("Gap", XMLNS_DETAILS))

    idEnt = Element("idEnt")

    idEnt.append(_new_element("anDoi", text=str(duration_flag_to_int(donor.two_years))))
    idEnt.append(_new_element("cifOJ", text=donor.ngo.registration_number, clean="numbers"))
    idEnt.append(_new_element("denOJ", text=donor.ngo.name, clean="alnum"))
    idEnt.append(_new_element("ibanNp", text=donor.cause.bank_account, clean="alnum"))
    idEnt.append(_new_element("prc", text="3.50"))
    idEnt.append(_new_element("venitB"))
    idEnt.append(_new_element("acord", text="1" if donor.anaf_gdpr else "0"))
    ent.append(idEnt)

    return ent
