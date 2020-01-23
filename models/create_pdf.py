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
image_path = "/static/images/formular.jpg"

def add_donor_data(c, person):
    
    # the first name
    if len(person["first_name"]) > 18:
        c.setFontSize(12)

    donor_block_x = 673

    c.drawString(67, donor_block_x, person["first_name"])
    c.setFontSize(default_font_size)

    # father's first letter
    c.drawString(300, donor_block_x, person["father"])

    # the last name
    last_name = person["last_name"]
    if len(last_name) > 34:
        c.setFontSize(10)

    c.drawString(67, donor_block_x-23, last_name)


    # =======================================
    # THIRD ROW
    # 
    third_row_x = donor_block_x - 45

    # the street
    street = person["street"]

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

    # telephone
    if person['tel']:
        c.setFontSize(12)
        c.drawString(start_email_x, third_row_x - 15, person['tel'])
    

    c.setFontSize(default_font_size)

    # first x mark
    # Venituri din salarii si asimilate salariilor
    # pension
    # if person['income'] == 'pension':
    #     c.drawString(172, donor_block_x - 162, "x")
    # # wage
    # else:
    #     c.drawString(172, donor_block_x - 145, "x")


def add_ngo_data(c, ong):
    start_ong_x = 440

    # the x mark
    c.drawString(218, start_ong_x, "x")
    # the cif code
    c.setFontSize(9)
    start_cif = start_ong_x - 39
    c.drawString(245, start_cif, ong["cif"])

    org_name = ong["name"]
    if len(org_name) > 79:
        c.setFontSize(9)
    elif len(org_name) > 65:
        c.setFontSize(12)

    # ngo name
    c.drawString(180, start_ong_x - 61, org_name.encode('utf-8'))

    c.setFontSize(11)

    account = ong["account"]
    for i, l in enumerate(account):
        if i%5 == 0:
            account = account[:i] + " " + account[i:]

    c.drawString(106, start_ong_x - 83, account)

def add_special_status_ngo_data(c, ong):
    """Used to add data for NGOs with a special status: they received 3,5% not 2"""

    start_ong_x = 319

    # the x mark
    c.drawString(538, start_ong_x, "x")
    # the cif code
    c.setFontSize(9)
    c.drawString(492, start_ong_x - 40, ong["cif"])

    try:
        org_name = ong["name"].encode('utf-8')
    except Exception as e:
        org_name = ong["name"]

    # crop the text at max 60 length
    org_name = org_name[:60]

    # if the name is too long
    # split it in two rows
    if len(org_name) > 27:
        first_row = ""
        second_row = ""

        arr = org_name.split(" ")
        for i in range(0, len(arr) + 1):
            first_row = " ".join(arr[0: i+1])
            if len(first_row) > 28:
                first_row = " ".join(arr[0: i])
                second_row = " ".join(arr[i: len(arr)])
                break

        c.setFontSize(8)
        c.drawString(250, start_ong_x - 35, first_row)
        c.drawString(250, start_ong_x - 42, second_row)
    else:
        c.drawString(250, start_ong_x - 40, org_name)

    c.setFontSize(11)

    account = ong["account"]
    for i, l in enumerate(account):
        if i%5 == 0:
            account = account[:i] + " " + account[i:]

    c.drawString(104, start_ong_x - 63, account)

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
    start_x = 305
    for letter in year:
        c.drawString(start_x, 734, letter)
        start_x += 18

    # DRAW DONOR DATA
    if person:
        add_donor_data(c, person)

    # DRAW ONG DATA
    # if the ngo has a special status, the form is completed differently
    if ong['special_status']:
        add_special_status_ngo_data(c, ong)
    else:
        add_ngo_data(c, ong)

    c.save()

    # go to the beginning of the file
    packet.seek(0)
    # packet.type = "application/pdf"

    return packet