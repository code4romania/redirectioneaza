$(function () {
    var canvas = document.getElementById("signature")
    var twpPercWrapper = document.querySelector('.signature-container')
    var clearButton = $('#clear-signature')
    var signatureInput = $('#signature-input')

    signaturePad = null

    var resizeCanvas = function() {
        canvas.width = twpPercWrapper.clientWidth;
        canvas.height = 300;

        signaturePad = new SignaturePad(canvas,
            {
                backgroundColor: 'rgb(255,255,255)',
                drawOnly: true,
                lineTop: 200,
                penWidth: 1,
                lineWidth: 1
            }
        );
    }

    resizeCanvas();

    window.addEventListener('resize', resizeCanvas, false);

    clearButton.on('click', function(){
        signaturePad.clear();
    });

    $(window).on('submit', function (ev) {
        signatureInput.val(signaturePad.toDataURL("image/svg+xml"))
    })
})