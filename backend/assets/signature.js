import SignaturePad from 'signature_pad';

let canvas = document.getElementById("signature");

let signatureInput = document.getElementById("signature-input");

let clearButton = document.getElementById("signature-reset");
let sendButton = document.getElementById("signature-send");

let signaturePad = new SignaturePad(canvas, {
  backgroundColor: 'transparent'
});

function resizeCanvas() {
  // Only run when the canvas is visible
  if (canvas.offsetWidth === 0 || canvas.offsetHeight === 0) {
    return;
  }

  const ratio = Math.max(window.devicePixelRatio || 1, 1);

  // This part causes the canvas to be cleared
  canvas.width = canvas.offsetWidth * ratio;
  canvas.height = canvas.offsetHeight * ratio;

  canvas.getContext("2d").scale(ratio, ratio);

  signaturePad.clear();
}

// When the canvas offsetWidth or offsetHeight changes, resize the canvas
new ResizeObserver(resizeCanvas).observe(canvas);

clearButton.addEventListener("click", function (event) {
  signaturePad.clear();
});

sendButton.addEventListener("click", function (event) {
  if (!signaturePad.isEmpty()) {
    signatureInput.value = signaturePad.toDataURL('image/svg+xml');
  }
});

export default signaturePad;
