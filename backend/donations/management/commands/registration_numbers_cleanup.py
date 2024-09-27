import re
from typing import Dict, List, Optional

from django.core.exceptions import ValidationError
from django.core.management import BaseCommand

from donations.models.main import Ngo, ngo_id_number_validator


class Command(BaseCommand):
    help = "Clean up registration numbers for all NGOs."

    registration_number_pattern = r"^(RO|)\d{1,10}$"
    registration_number_with_vat_id_pattern = r"^RO\d{1,10}$"

    def handle(self, *args, **options):
        errors: List[str] = []
        # for ngo_id in Ngo.objects.filter(registration_number_valid=None).values_list("pk", flat=True):
        for ngo_id in Ngo.objects.filter(registration_number_valid=False).values_list("pk", flat=True):
            result = self.clean_ngo(ngo_id)

            if result["state"] != "success":
                errors.append(f"[{result['registration_number']} — {result['state']}]")

        if errors:
            self.stdout.write(
                self.style.ERROR(f"Errors occurred while cleaning registration numbers for NGOs: ({','.join(errors)})")
            )

        return f"Errors occurred while cleaning registration numbers for NGOs: ({','.join(errors)})"

    def clean_ngo(self, ngo_id: int) -> Dict[str, str]:
        ngo = Ngo.objects.get(pk=ngo_id)

        try:
            return self.clean_ngo_registration_number(ngo)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error while cleaning NGO {ngo.pk}: {e}"))

            return {
                "state": "error",
                "registration_number": ngo.registration_number,
                "message": f"Error while cleaning NGO {ngo.pk}: {e}",
            }

    def clean_ngo_registration_number(self, ngo: Ngo) -> Dict[str, str]:
        initial_registration_number = ngo.registration_number
        cleaned_registration_number = self._clean_registration_number(initial_registration_number)

        if not re.match(self.registration_number_pattern, cleaned_registration_number):
            self.stdout.write(
                self.style.ERROR(f"NGO {ngo.pk} has an invalid registration number: {ngo.registration_number}")
            )

            ngo.registration_number_valid = False
            ngo.save()

            return {
                "state": "invalid",
                "registration_number": ngo.registration_number,
                "message": f"NGO {ngo.pk} has an invalid registration number: {ngo.registration_number}",
            }

        if cleaned_registration_number:
            matching_ngos = Ngo.objects.filter(registration_number=cleaned_registration_number).exclude(pk=ngo.pk)
            if matching_ngos.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"NGO {ngo.pk} has a duplicate registration number(s): "
                        f"{matching_ngos.values_list('pk', flat=True)}"
                    )
                )

                return {
                    "state": "duplicate",
                    "registration_number": ngo.registration_number,
                    "message": (
                        f"NGO {ngo.pk} has a duplicate registration number(s): "
                        f"{matching_ngos.values_list('pk', flat=True)}"
                    ),
                }

        vat_information = self._extract_vat_id(cleaned_registration_number)

        ngo.vat_id = vat_information["vat_id"]
        ngo.registration_number = vat_information["registration_number"]
        ngo.registration_number_valid = self._validate_registration_number(ngo.registration_number)

        ngo.save()

        return {
            "state": "success",
            "registration_number": ngo.vat_id + ngo.registration_number,
            "message": (
                f"NGO {ngo.pk} registration number cleaned: "
                f"{vat_information['vat_id']} {vat_information['registration_number']}"
            ),
        }

    def _clean_registration_number(self, reg_num: str) -> Optional[str]:
        if re.match(self.registration_number_pattern, reg_num):
            return reg_num

        # uppercase the string and strip of any whitespace
        reg_num = reg_num.upper().strip()

        # remove all the whitespace
        reg_num = re.sub(r"\s+", "", reg_num)

        return reg_num

    def _extract_vat_id(self, reg_num: str) -> Dict[str, str]:
        result = {
            "vat_id": "",
            "registration_number": reg_num,
        }

        # if the registration number matches the RO########## pattern separate the VAT ID from the CUI
        if re.match(self.registration_number_with_vat_id_pattern, reg_num):
            result["vat_id"] = reg_num[:2]
            result["registration_number"] = reg_num[2:]

        return result

    @staticmethod
    def _validate_registration_number(reg_num: str) -> bool:
        try:
            ngo_id_number_validator(reg_num)
        except ValidationError:
            return False

        return True
