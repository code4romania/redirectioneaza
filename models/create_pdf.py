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


#keep for later
default_font_size = 15
# image_name = "/images/2.jpg"
image_path = "/static/images/2.jpg"

def add_donor_data(c, person):
    
    # the first name
    if len(person["first_name"]) > 18:
        c.setFontSize(12)

    donor_block_x = 668

    c.drawString(66, donor_block_x, person["first_name"])
    c.setFontSize(default_font_size)

    # father's first letter
    c.drawString(299, donor_block_x, person["father"])

    # the last name
    last_name = person["last_name"]
    if len(last_name) > 34:
        c.setFontSize(10)

    c.drawString(66, donor_block_x-25, last_name)


    # =======================================
    # THIRD ROW
    # 
    third_row_x = donor_block_x - 49

    # the street
    street = person["street"]
    if len(street) > 40:
        c.setFontSize(8)
    elif len(street) in range(36, 40):
        c.setFontSize(10)
    elif len(street) in range(25, 35):
        c.setFontSize(12)

    c.drawString(66, third_row_x, street)
    c.setFontSize(default_font_size)

    # numar
    c.drawString(289, third_row_x, person["number"])
    # 
    # =======================================

    # =======================================
    # FOURTH ROW
    fourth_row_x = donor_block_x - 73

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
    c.drawString(68, donor_block_x - 98, person["city"])

    c.setFontSize(16)

    # cnp
    start_x = 336
    for letter in person["cnp"]:
        c.drawString(start_x, donor_block_x - 10, letter)
        start_x += 18.4


    # email
    start_email_x = 368
    if person['email']:
        if len(person['email']) < 32:
            c.setFontSize(12)
        elif len(person['email']) < 40:
            c.setFontSize(10)
        else:
            c.setFontSize(8)

        c.drawString(start_email_x, third_row_x + 12, person['email'])

    #telephone
    if person['tel']:
        c.setFontSize(12)
        c.drawString(start_email_x, third_row_x - 15, person['tel'])
    

    c.setFontSize(default_font_size)

    # first x mark
    # Venituri din salarii si asimilate salariilor
    c.drawString(171, donor_block_x - 145, "x")    

def add_ngo_data(c, ong):
    start_ong_x = 373

    # the x mark
    c.drawString(221, start_ong_x, "x")
    # the cif code
    c.drawString(409, start_ong_x - 1, ong["cif"])

    org_name = ong["name"]
    if len(org_name) > 79:
        c.setFontSize(10)
    elif len(org_name) > 65:
        c.setFontSize(13)

    c.drawString(118, start_ong_x - 24, org_name.encode('utf-8'))

    c.setFontSize(11)

    account = ong["account"]
    for i, l in enumerate(account):
        if i%5 == 0:
            account = account[:i] + " " + account[i:]

    c.drawString(118, start_ong_x - 48, account)

def create_pdf(person, ong):
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
    background = ImageReader( abs_path + image_path )
    c.drawImage(background, 0, 0, width=width, height=height)

    # the default font size
    # info(c.getAvailableFonts())
    c.setFont('OpenSans', default_font_size)
    c.setFontSize(default_font_size)

    # the year
    # this is the previous year, starting from 1 Jan until - 25 May ??
    year = str( datetime.now().year - 1 )
    start_x = 306
    for letter in year:
        c.drawString(start_x, 727, letter)
        start_x += 17

    # DRAW DONOR DATA
    if person:
        add_donor_data(c, person)

    # DRAW ONG DATA
    add_ngo_data(c, ong)

    c.save()

    # go to the beginning of the file
    packet.seek(0)
    # packet.type = "application/pdf"

    return packet