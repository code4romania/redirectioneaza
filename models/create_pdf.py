import os

import tempfile

from google.appengine.api import app_identity

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from datetime import datetime

from logging import info

abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
font_path = abs_path + "/static/font/opensans.ttf"
pdfmetrics.registerFont(TTFont('OpenSans', font_path))


default_font_size = 15
form_image_path = "/static/images/formular-2021.jpg"


def format_ngo_account(ngo_account):
    # remove white spaces from account
    ngo_account = ngo_account.replace(' ', '')

    account = ''
    for i, l in enumerate(ngo_account):
        account += l
        if (i + 1) % 4 == 0:
            account += " "

    return account

def add_donor_data(c, person):

    donor_block_x = 681

    # the first name
    if len(person["first_name"]) > 18:
        c.setFontSize(12)

    c.drawString(75, donor_block_x, person["first_name"])
    c.setFontSize(default_font_size)

    # father's first letter
    c.drawString(300, donor_block_x, person["father"])

    # the last name
    last_name = person["last_name"]
    if len(last_name) > 34:
        c.setFontSize(10)

    c.drawString(75, donor_block_x - 22, last_name)


    # =======================================
    # THIRD ROW
    # 
    third_row_x = donor_block_x - 45

    # the street
    street = person["street"]
    info(len(street))
    if len(street) > 40:
        c.setFontSize(8)
    elif len(street) in range(36, 41):
        c.setFontSize(10)
    elif len(street) in range(24, 36):
        c.setFontSize(11)

    c.drawString(67, third_row_x, street)
    c.setFontSize(default_font_size)

    # numar
    if len(person["number"]) > 5:
        c.setFontSize(8)
    elif len(person["number"]) > 3:
        c.setFontSize(10)

    c.drawString(289, third_row_x, person["number"])
    c.setFontSize(default_font_size)

    # 
    # =======================================

    # =======================================
    # FOURTH ROW
    fourth_row_x = donor_block_x - 67

    c.setFontSize(14)
    # bloc
    c.drawString(49, fourth_row_x, person["bl"])
    # scara
    c.drawString(108, fourth_row_x, person["sc"])

    # etaj
    c.drawString(150, fourth_row_x, person["et"])

    # apartament
    c.drawString(185, fourth_row_x, person["ap"])

    # judet
    if len(person["county"]) <= 12:
        c.setFontSize(12)
    else:
        c.setFontSize(8)
    
    c.drawString(255, fourth_row_x, person["county"])
    c.setFontSize(default_font_size)
    # 
    # =======================================


    # oras
    c.drawString(69, donor_block_x - 90, person["city"])

    c.setFontSize(16)

    # cnp
    start_x = 336
    for letter in person["cnp"]:
        c.drawString(start_x, donor_block_x - 10, letter)
        start_x += 18.5


    # email
    start_email_x = 368
    if person['email']:
        if len(person['email']) < 32:
            c.setFontSize(12)
        elif len(person['email']) < 40:
            c.setFontSize(10)
        else:
            c.setFontSize(8)

        c.drawString(start_email_x, third_row_x + 14, person['email'])

    # telephone
    if person['tel']:
        c.setFontSize(12)
        c.drawString(start_email_x, third_row_x - 15, person['tel'])
    

    c.setFontSize(default_font_size)

def add_ngo_data(c, ong):
    start_ong_y = 449

    # the x mark
    c.drawString(219, start_ong_y, "x")

    if ong.get('two_years'):
        c.drawString(325, start_ong_y - 21, "x")

    # the cif code
    c.setFontSize(9)
    c.drawString(250, start_ong_y - 41, ong["cif"])

    # the name
    org_name = ong["name"]
    if len(org_name) > 79:
        c.setFontSize(9)
    elif len(org_name) > 65:
        c.setFontSize(12)

    c.drawString(186, start_ong_y - 64, org_name.encode('utf-8'))

    c.setFontSize(11)

    # the bank account
    account = format_ngo_account(ong["account"])
    c.drawString(110, start_ong_y - 86, account)

def create_pdf(person = {}, ong = {}):
    """method used to create the pdf

    person: dict with the person's data 
        first_name
        father
        last_name
        email
        tel
        street
        number
        bl
        sc
        et
        ap
        county
        city
        cnp


    ong: dict with the ngo's data
        name
        cif
        account
    """
    
    # packet = StringIO.StringIO()
    # we could also use StringIO
    packet = tempfile.TemporaryFile(mode='w+b')
    
    c = canvas.Canvas(packet, A4)
    width, height = A4
    
    # add the image as background
    background = ImageReader( abs_path + form_image_path )
    c.drawImage(background, 0, 0, width=width, height=height)

    c.setFont('OpenSans', default_font_size)
    c.setFontSize(default_font_size)

    # the year
    # this is the previous year
    year = str( datetime.now().year - 1 )
    start_x = 305
    for letter in year:
        c.drawString(start_x, 736, letter)
        start_x += 18

    # DRAW DONOR DATA
    if person.get('first_name'):
        add_donor_data(c, person)

    add_ngo_data(c, ong)

    c.save()

    # go to the beginning of the file
    packet.seek(0)
    # packet.type = "application/pdf"

    return packet
