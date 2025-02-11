import SignaturePad from 'signature_pad';

const placeholder = 'data:image/gif;base64,R0lGODlhAwABAIAAAP///wAAACH5BAEAAAAALAAAAAADAAEAAAIChAsAOw==';

export default function() {
  return {
    signaturePad: null,
    signatureInput: null,
    signaturePreview: null,
    canvas: null,
    resizeCanvas() {
      // Only run when the canvas is visible
      if (this.canvas.offsetWidth === 0 || this.canvas.offsetHeight === 0) {
        return;
      }

      const ratio = Math.max(window.devicePixelRatio || 1, 1);

      // This part causes the canvas to be cleared
      this.canvas.width = this.canvas.offsetWidth * ratio;
      this.canvas.height = this.canvas.offsetHeight * ratio;

      this.canvas.getContext("2d").scale(ratio, ratio);

      this.clearSignature();
    },

    init() {
      this.canvas = document.getElementById('signatureCanvas');

      this.signatureInput = document.getElementById("signature-input");
      this.signaturePreview = document.getElementById("signature-preview");

      try {
        this.signaturePad = new SignaturePad(this.canvas, {
          backgroundColor: 'transparent'
        });
      } catch (e) {
        if (e instanceof ReferenceError) {
          // SignaturePad is not available yet so retry the init soon
          setTimeout(() => this.init(), 1000);
          return;
        } else {
          throw e;
        }
      }

      if (!this.signatureInput.value) {
        this.clearSignature();
      }


      // When the canvas offsetWidth or offsetHeight changes, resize the canvas
      new ResizeObserver(() => this.resizeCanvas()).observe(this.canvas);
    },
    saveSignature() {
      if (!this.signaturePad.isEmpty()) {
        this.signatureInput.value = this.signaturePad.toDataURL('image/svg+xml');
        this.signaturePreview.src = this.signaturePad.toDataURL('image/svg+xml');

        let event = new Event('input');
        this.signatureInput.dispatchEvent(event);
      }
    },
    clearSignature() {
      this.signaturePreview.src = placeholder;
      this.signaturePad.clear();
    }
  }
}
