from datetime import datetime
from xml.etree.ElementTree import Element

from donations.common.validation.phone_number import clean_phone_number
from donations.models.donors import Donor

from donations.models.ngos import Cause
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


def new_xml_element(tag: str, text: str = None, clean: str = "") -> Element:
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


def build_btn_doc() -> Element:
    element = Element("btnDoc")

    element.append(Element("btnSalt"))
    element.append(Element("btnWebService"))

    info = Element("info")
    info.append(Element("help", XMLNS_DETAILS))

    element.append(info)

    return element


def build_id_doc_from_raw(ngo_cui: str, timestamp: datetime) -> Element:
    element = Element("IdDoc")

    element.append(new_xml_element(tag="universalCode", text=ANAF_FORM_VERSION))

    totalPlata_A = Element("totalPlata_A")
    element.append(totalPlata_A)

    element.append(new_xml_element(tag="cif", text=ngo_cui, clean="numbers"))
    element.append(new_xml_element(tag="formValid", text="FORMULAR NEVALIDAT"))
    element.append(new_xml_element(tag="luna_r", text="12"))
    element.append(new_xml_element(tag="d_rec", text="0"))
    element.append(new_xml_element(tag="an_r", text=str(timestamp.year - 1)))

    return element


def build_imp() -> Element:
    element = Element("imp")

    bifaI = Element("bifaI")
    bifaI.append(new_xml_element(tag="rprI", text="0"))

    element.append(bifaI)

    return element


def build_borderou_data(xml_index: int, timestamp: datetime, cause: Cause) -> Element:
    return build_borderou_data_from_raw(
        xml_index=xml_index,
        timestamp=timestamp,
        bank_account=cause.bank_account,
        ngo_name=cause.ngo.name,
        ngo_registration_number=cause.ngo.registration_number,
        ngo_address=cause.ngo.address,
        ngo_locality=cause.ngo.locality,
        ngo_county=cause.ngo.county,
    )


def build_borderou_data_from_raw(
    *,
    xml_index: int,
    timestamp: datetime,
    bank_account: str,
    ngo_name: str,
    ngo_registration_number: str,
    ngo_address: str,
    ngo_locality: str = None,
    ngo_county: str = None,
) -> Element:
    element = Element("nrDataB")

    element.append(new_xml_element(tag="nrD", text=str(xml_index)))
    element.append(new_xml_element(tag="dataD", text=timestamp.strftime("%d.%m.%Y")))
    element.append(new_xml_element(tag="denD", text=ngo_name, clean="alnums"))
    element.append(new_xml_element(tag="cifD", text=ngo_registration_number, clean="numbers"))

    ngo_address: str = ngo_address
    if ngo_locality:
        ngo_address += ", " + ngo_locality
    if ngo_county:
        ngo_address += ", " + ngo_county
    element.append(new_xml_element(tag="adresaD", text=ngo_address, clean="custom"))

    element.append(new_xml_element(tag="ibanD", text=bank_account, clean="alnum"))

    return element


def build_donor(index: int, donor: Donor) -> Element:
    return build_donor_raw(
        index=index,
        ngo_cui=donor.ngo.registration_number,
        ngo_name=donor.ngo.name,
        bank_account=donor.cause.bank_account,
        donor_cnp=donor.get_cnp(),
        donor_last_name=donor.l_name,
        donor_first_name=donor.f_name,
        donor_initial=donor.initial,
        donor_address=donor.get_address(include_full=True)["full_address"],
        donor_phone=donor.phone,
        donor_email=donor.email,
        donor_anaf_gdpr="1" if donor.anaf_gdpr else "0",
        donor_period=str(duration_flag_to_int(donor.two_years) if donor.two_years else 1),
    )


def build_donor_raw(
    *,
    index: int,
    ngo_cui: str,
    ngo_name: str,
    bank_account,
    donor_cnp: str,
    donor_last_name: str = None,
    donor_first_name: str = None,
    donor_initial: str = None,
    donor_address: str = None,
    donor_phone: str = None,
    donor_email: str = None,
    donor_anaf_gdpr: str = "0",
    donor_period: str = "1",
) -> Element:
    element = Element("contrib")

    nrCrt = Element("nrCrt")
    nrCrt.append(new_xml_element("nV", str(index + 1)))
    element.append(nrCrt)

    contributor_identity = Element("idCnt")
    contributor_identity.append(new_xml_element(tag="nume", text=donor_last_name.upper(), clean="alphabets"))
    contributor_identity.append(new_xml_element(tag="init", text=donor_initial.upper(), clean="alphabet"))
    contributor_identity.append(new_xml_element(tag="pren", text=donor_first_name.upper(), clean="alphabets"))
    contributor_identity.append(new_xml_element(tag="cif_c", text=donor_cnp, clean="numbers"))
    contributor_identity.append(new_xml_element(tag="adresa", text=donor_address, clean="custom"))
    contributor_identity.append(new_xml_element(tag="telefon", text=clean_phone_number(donor_phone), clean="numbers"))
    contributor_identity.append(new_xml_element(tag="fax"))
    contributor_identity.append(new_xml_element(tag="email", text=donor_email, clean="email"))
    element.append(contributor_identity)

    s15 = Element("s15")
    contribution_data = Element("date")
    contribution_data.append(nrCrt)

    contribution_data.append(_build_donor_field_sum_option())
    contribution_data.append(_build_donor_field_bursa())
    contribution_data.append(
        _build_donor_field_entitate_raw(
            ngo_cui=ngo_cui,
            ngo_name=ngo_name,
            bank_account=bank_account,
            donor_anaf_gdpr=donor_anaf_gdpr,
            donor_period=donor_period,
        )
    )

    s15.append(contribution_data)
    element.append(s15)

    return element


def _build_donor_field_sum_option():
    optiuneSuma = Element("optiuneSuma")
    slct = Element("slct")
    slct.append(new_xml_element("ent", text="1"))
    slct.append(new_xml_element("brs", text="0"))
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
    nrDataP.append(new_xml_element("venitB"))
    idEnt.append(nrDataP)

    brs.append(idEnt)

    return brs


def _build_donor_field_entitate_raw(
    ngo_cui: str,
    ngo_name: str,
    bank_account: str,
    donor_anaf_gdpr: str = "0",
    donor_period: str = "1",
):
    ent = Element("ent")

    ent.append(Element("Gap", XMLNS_DETAILS))

    idEnt = Element("idEnt")

    idEnt.append(new_xml_element("anDoi", text=donor_period))
    idEnt.append(new_xml_element("cifOJ", text=ngo_cui, clean="numbers"))
    idEnt.append(new_xml_element("denOJ", text=ngo_name, clean="alnum"))
    idEnt.append(new_xml_element("ibanNp", text=bank_account, clean="alnum"))
    idEnt.append(new_xml_element("prc", text="3.50"))
    idEnt.append(new_xml_element("venitB"))
    idEnt.append(new_xml_element("acord", text=donor_anaf_gdpr))
    ent.append(idEnt)

    return ent
