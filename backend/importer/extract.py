"""
Extract the CNP and Address from the PDF form

TODO: Integrate this with Django as a management command and use Django's FileField
"""

from collections import namedtuple
from functools import partial
from io import BytesIO
from pypdf import PdfReader


Zone = namedtuple("Zone", ["start_y", "start_x", "end_x"])


data_zones = {
    "cnp": Zone(671, 336, 0),
    "father": Zone(681, 300, 336),
    "street_name": Zone(636, 67, 289),
    "street_number": Zone(636, 289, 368),
    "street_bl": Zone(614, 49, 108),
    "street_sc": Zone(614, 108, 150),
    "street_et": Zone(614, 150, 185),
    "street_ap": Zone(614, 185, 255),
    "percent": Zone(341, 146, 186),
}


def _visitor_builder(parts, start_x, start_y, end_x, text, cm, tm, fontDict, fontSize):
    # print(tm, text)  # Print the text matrix (for debugging)
    x = tm[4]
    y = tm[5]
    # Check that the text is on the required line
    if x >= start_x and y == start_y:
        # Check that the text doesn't run over the end position
        if (end_x and x < end_x) or not end_x:
            parts.append(text.strip())


def extract_data(page, zone: Zone):
    parts = []
    visitor = partial(_visitor_builder, parts, zone.start_x, zone.start_y, zone.end_x)
    page.extract_text(0, extraction_mode="plain", visitor_text=visitor)
    return "".join(parts)


if __name__ == "__main__":
    # This "open" to be replaced with Django's FileField.open()
    pdf_file = open("document.pdf", "rb")

    reader = PdfReader(BytesIO(pdf_file.read()))
    page = reader.pages[0]

    print("CNP =", extract_data(page, data_zones["cnp"]))
    print("Father =", extract_data(page, data_zones["father"]))

    print("Street Name =", extract_data(page, data_zones["street_name"]))
    print("Street Number =", extract_data(page, data_zones["street_number"]))
    print("BL =", extract_data(page, data_zones["street_bl"]))
    print("SC =", extract_data(page, data_zones["street_sc"]))
    print("ET =", extract_data(page, data_zones["street_et"]))
    print("AP =", extract_data(page, data_zones["street_ap"]))

    print("Percent =", extract_data(page, data_zones["percent"]))

    pdf_file.close()
