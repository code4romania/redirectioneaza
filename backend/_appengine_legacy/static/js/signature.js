$(function () {
    var canvas = document.getElementById("signature")
    var twpPercWrapper = document.querySelector('.signature-container')
    var clearButton = $('#clear-signature')
    var signatureInput = $('#signature-input')

    signaturePad = null

    var resizeCanvas = function() {
        var data = signaturePad.toData();
        var ratio = Math.max(window.devicePixelRatio || 1, 1);

        canvas.width = canvas.offsetWidth * ratio;
        canvas.height = canvas.offsetHeight * ratio;
        canvas.getContext('2d').scale(ratio, ratio);

        signaturePad.clear()
        signaturePad.fromData(data)
    }

    signaturePad = new SignaturePad(canvas,
        {
            backgroundColor: 'transparent',
            penColor: '#354A8F',
            drawOnly: true,
            lineTop: 200,
            penWidth: 1,
            lineWidth: 1
        }
    );

    resizeCanvas();

    window.addEventListener('resize', resizeCanvas, false);

    clearButton.on('click', function(){
        signaturePad.clear();
    });

    $(window).on('submit', function (ev) {
        signatureInput.val(signaturePad.toDataURL("image/svg+xml"))
    })
})