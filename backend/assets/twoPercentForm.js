export default function() {
  return {
    form: undefined,
    pristine: undefined,

    confirmationModalIsOpen: false,
    signatureModalIsOpen: false,
    validateSignature: false,
    init() {
      this.form = document.getElementById("two-percent-form");
      this.signatureInput = document.getElementById("signature-input");
      this.signaturePreview = document.getElementById("signature-preview");

      this.pristine = new Pristine(this.form, {
        errorTextClass: "mt-2 text-sm text-red-600",
        errorClass: "has-error",
        successClass: "has-success"
      });

      this.pristine.addValidator(this.signatureInput, (value) => {
        if (this.validateSignature) {
          return value.length > 0;
        } else {
          return true;
        }
      }, "Acest câmp este obligatoriu", 2, false);
    },
    sendSignedForm() {
      this.validateSignature = true;
      if (this.pristine.validate()) {
        this.form.submit();
      }
    },
    sendUnsignedForm() {
      this.validateSignature = false;
      if (this.pristine.validate()) {
        this.confirmationModalIsOpen = true;
      }
    },
    sendFormWithoutSignatureField() {
      this.validateSignature = false;
      if (this.pristine.validate()) {
        this.form.submit();
      }
    },
    clearSignature() {
      // dispatch an input event when we clear the signature so it will revalidate the form
      this.signaturePreview.src = "";
      this.signatureInput.value = "";

      let event = new Event('input');
      this.signatureInput.dispatchEvent(event);
    }
  }
}
