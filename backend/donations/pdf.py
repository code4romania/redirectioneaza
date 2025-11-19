import base64
import os
import tempfile
from datetime import datetime
from io import BytesIO

from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.pdfgen.canvas import Canvas
from svglib.svglib import svg2rlg

from donations.models.donors import Donor
from donations.models.ngos import Cause, Ngo

abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
# TODO: we might need to rethink this; we should not hardcode the path to static_extras
font_path = abs_path + "/static_extras/font/opensans.ttf"
pdfmetrics.registerFont(TTFont("OpenSans", font_path))

default_font_size = 15
form_image_path = abs_path + "/static_extras/images/formular-2025.jpg"


def _format_bank_account(bank_account: str):
    # remove spaces from the bank account number
    bank_account = bank_account.replace(" ", "")

    account = ""
    for i, letter in enumerate(bank_account):
        account += letter
        if (i + 1) % 4 == 0:
            account += " "

    return account


def _add_ngo_data(start_y, c: Canvas, cause: Cause | None, ngo: Ngo):
    start_ngo_y = start_y - 289

    # the x mark to support an NGO
    c.drawString(220, start_ngo_y, "x")

    # the cif code
    c.setFontSize(9)
    c.drawString(250, start_ngo_y - 39, ngo.full_registration_number)

    # the name
    org_name = ngo.name
    if len(org_name) > 79:
        c.setFontSize(9)
    elif len(org_name) > 65:
        c.setFontSize(12)

    c.drawString(186, start_ngo_y - 62, org_name)

    c.setFontSize(11)

    # the bank account
    bank_account = cause.bank_account if cause else ngo.bank_account
    account = _format_bank_account(bank_account)
    c.drawString(110, start_ngo_y - 84, account)

    c.drawString(146, start_ngo_y - 106, "3,5%")


def _add_donor_data(start_y, c: Canvas, donor: Donor):
    donor_block_x = 70
    donor_block_y = start_y - 57

    # father's initial
    c.drawString(donor_block_x + 230, donor_block_y, donor.initial)

    # the last name
    last_name = donor.l_name
    if len(last_name) > 34:
        c.setFontSize(10)

    c.drawString(donor_block_x, donor_block_y, last_name)

    # the first name
    first_name = donor.f_name
    if len(first_name) > 18:
        c.setFontSize(12)

    c.drawString(donor_block_x, donor_block_y - 23, first_name)

    c.setFontSize(default_font_size)

    # =======================================
    # THIRD ROW
    #
    third_row_y = donor_block_y - 45

    # the street
    donor_address: dict = donor.get_address()

    street = donor_address["str"]
    if len(street) > 40:
        c.setFontSize(8)
    elif 36 < len(street) < 41:
        c.setFontSize(10)
    elif 24 < len(street) < 36:
        c.setFontSize(11)

    c.drawString(67, third_row_y, street)
    c.setFontSize(default_font_size)

    # număr
    street_number = donor_address["nr"]
    if len(street_number) > 5:
        c.setFontSize(8)
    elif len(street_number) > 3:
        c.setFontSize(10)

    c.drawString(289, third_row_y, street_number)
    c.setFontSize(default_font_size)

    #
    # =======================================

    # =======================================
    # FOURTH ROW
    fourth_row_y = donor_block_y - 67

    c.setFontSize(14)
    # bloc
    c.drawString(donor_block_x - 21, fourth_row_y, str(donor_address.get("bl", "")))
    # scara
    c.drawString(donor_block_x + 38, fourth_row_y, str(donor_address.get("sc", "")))

    # etaj
    c.drawString(donor_block_x + 80, fourth_row_y, str(donor_address.get("et", "")))

    # apartament
    c.drawString(donor_block_x + 115, fourth_row_y, str(donor_address.get("ap", "")))

    # județ
    county = donor.county
    if len(str(county)) <= 12:
        c.setFontSize(12)
    else:
        c.setFontSize(8)

    if len(str(county)) == 1:
        county = f"Sector {county}"

    c.drawString(donor_block_x + 185, fourth_row_y, county)
    c.setFontSize(default_font_size)
    #
    # =======================================

    # oras
    c.drawString(donor_block_x, donor_block_y - 90, donor.city)

    c.setFontSize(16)

    # cnp
    cnp_x = donor_block_x + 266
    cnp_y = donor_block_y - 10

    cnp = donor.get_cnp()
    for letter in cnp:
        c.drawString(cnp_x, cnp_y, letter)
        cnp_x += 18.5

    # email
    start_email_x = donor_block_x + 296
    email = donor.email
    if email:
        if len(email) < 32:
            c.setFontSize(12)
        elif len(email) < 40:
            c.setFontSize(10)
        else:
            c.setFontSize(8)

        c.drawString(start_email_x, donor_block_y - 32, email)

    # telephone
    phone_number = donor.phone
    if phone_number:
        c.setFontSize(12)
        c.drawString(start_email_x, donor_block_y - 59, phone_number)

    c.setFontSize(default_font_size)

    if donor.two_years:
        c.drawString(donor_block_x + 256, donor_block_y - 253, "x")

    if donor.anaf_gdpr:
        c.drawString(donor_block_x - 39, donor_block_y - 362, "x")


def _add_signature_to_pdf(c, signature):
    # add the image as a background
    # remove the header added by JavaScript
    signature = signature.split(",")[1]

    # make sure the string has the right padding
    signature = signature + "=" * (-len(signature) % 4)
    base_image = base64.b64decode(signature)
    byte_image = BytesIO(base_image)

    # make this a svg2rlg object
    drawing = svg2rlg(byte_image)
    new_height = 30
    scaled_down = new_height / drawing.height

    # we want to scale the image down and stil keep its aspect ratio
    # the image might have dimensions of 750 x 200
    drawing.scale(scaled_down, scaled_down)

    # add it to the PDF
    renderPDF.draw(drawing, c, 166, 93)


def _initialize_pdf_canvas(packet):
    c: Canvas = canvas.Canvas(packet, A4)
    width, height = A4

    # add the image as a background
    background = ImageReader(form_image_path)

    c.drawImage(background, 0, 0, width=width, height=height)
    c.setFont("OpenSans", default_font_size)
    c.setFontSize(default_font_size)

    return c


def _add_year_to_pdf(c, start_x, start_y):
    # the year
    # this is the previous year
    year = str(datetime.now().year - 1)
    for letter in year:
        c.drawString(start_x, start_y, letter)
        start_x += 18


def create_cause_pdf(cause: Cause | None, ngo: Ngo):
    start_x = 305
    start_y = 726

    # packet = StringIO()
    # we could also use StringIO
    packet = tempfile.TemporaryFile(mode="w+b")

    c = _initialize_pdf_canvas(packet)

    _add_year_to_pdf(c, start_x, start_y)

    _add_ngo_data(start_y, c, cause, ngo)

    c.save()

    # go to the beginning of the file
    packet.seek(0)

    return packet


def create_full_pdf(donor: Donor, signature: str | None = None):
    """method used to create the PDF

    donor: Donor object with the person's data
    signature: base64 encoded string of the signature svg
    """

    start_x = 305
    start_y = 726

    # packet = StringIO()
    # we could also use StringIO
    packet = tempfile.TemporaryFile(mode="w+b")

    c = _initialize_pdf_canvas(packet)

    _add_year_to_pdf(c, start_x, start_y)

    # DRAW DONOR DATA
    _add_donor_data(start_y, c, donor)

    _add_ngo_data(start_y, c, donor.cause, donor.ngo)

    if signature:
        _add_signature_to_pdf(c, signature)

    c.save()

    # go to the beginning of the file
    packet.seek(0)

    return packet
