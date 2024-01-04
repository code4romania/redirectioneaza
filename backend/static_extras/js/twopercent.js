$(function () {

  $('.description').shorten({
    moreText: 'Arată mai mult',
    lessText: 'Arată mai puțin',
    showChars: 200
  });

  let errors = {
    server_error: "Se pare că am întâmpinat o eroare pe server. Vă rugăm încercați din nou.",
    fields_error: "Se pare că următoarele date sunt invalide: "
  }
  let ngoUrl = window.location.href;
  let form = $("#twopercent");

  let invalidFormAlert = $("#invalid-form-alert");
  let submitFormButton = $("#submit-twopercent-form");
  let signForm = $('#sign-form')
  let submitForm = $('.signature-container')

  let cnpField = $("#cnp")

  $('[data-toggle="popover"]').popover({
    trigger: "focus",
    placement: ($(window).width() > 790) ? "right" : "bottom"
  });

  let errorClass = "has-error";
  let invalidFields = {};

  function showError(context) {
    invalidFields[context.id] = true;

    let el = $(context);
    el.parent().addClass(errorClass);
    el.popover({
      content: "Valoarea acestui câmp este invalidă.",
      title: "",
      placement: ($(window).width() > 790) ? "right" : "bottom",
      trigger: "focus"
    });
  }

  function hideError(context) {
    delete invalidFields[context.id];

    let el = $(context);
    el.parent().removeClass(errorClass);
    el.popover('destroy');
  }

  $("#nume, #prenume, #strada, #bloc, #scara, #etaj, #ap, #localitate").on("blur", function () {
    let val = this.value;
    if (!val) return;

    let regex = /^[\w\s.\-ăîâșțşţ]+$/gi;
    // if we have no match
    if (!val.match(regex)) {
      showError(this);
    } else {
      hideError(this);
    }
  });

  /******************************************************************************/
  /****                            Validare CNP                              ****/

  /******************************************************************************/
  /**
   * Validate CNP ( valid for 1800-2099 )
   *
   * @return boolean
   * @param p_cnp
   */
  // copyright https://github.com/cristian-datu/CNP
  function validCNP(p_cnp) {
    let i = 0, year = 0, hashResult = 0, cnp = [], hashTable = [2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9];
    if (p_cnp.length !== 13) {
      return false;
    }
    for (i = 0; i < 13; i++) {
      cnp[i] = parseInt(p_cnp.charAt(i), 10);
      if (isNaN(cnp[i])) {
        return false;
      }
      if (i < 12) {
        hashResult = hashResult + (cnp[i] * hashTable[i]);
      }
    }
    hashResult = hashResult % 11;
    if (hashResult === 10) {
      hashResult = 1;
    }
    year = (cnp[1] * 10) + cnp[2];
    switch (cnp[0]) {
      case 1  :
      case 2 : {
        year += 1900;
      }
        break;
      case 3  :
      case 4 : {
        year += 1800;
      }
        break;
      case 5  :
      case 6 : {
        year += 2000;
      }
        break;
      case 7  :
      case 8 :
      case 9 : {
        year += 2000;
        if (year > (parseInt(new Date().getYear(), 10) - 14)) {
          year -= 100;
        }
      }
        break;
      default : {
        return false;
      }
    }
    if (year < 1800 || year > 2099) {
      return false;
    }
    return (cnp[12] === hashResult);
  }

  cnpField.on("blur", function () {
    let val = this.value;

    // if the user provided a value make sure it's valid
    if (val && !validCNP(val)) {
      showError(this);
    } else {
      hideError(this);
    }
  });

  $('#email').on('blur', function () {
    let email = $(this).val().trim();

    let regex = /[\w.-]+@[\w.-]+.\w+/
    if (email && !regex.test(email)) {
      showError(this);
    } else {
      hideError(this);
    }
  });

  $('#telefon').on('blur', function () {
    let telefon = $(this).val().trim();

    if (telefon && (telefon.length !== 10 || telefon.slice(0, 2) !== "07")) {
      showError(this);
    } else {
      hideError(this);
    }
  });

  signForm.on('click', function (ev) {
    let cnpVal = cnpField.val()

    if (!cnpVal) {
      ev.preventDefault()
      showError(cnpField)
      cnpField.focus()
    } else {
      if (!validCNP(cnpVal)) {
        ev.preventDefault()
        showError(cnpField)
        cnpField.focus()
      } else {
        // else, the form will be submitted
        hideError(cnpField)
        $('<input />').attr('type', 'hidden')
          .attr('name', "wants-to-sign").attr('value', 'True')
          .appendTo(form);
      }
    }
  })

  form.on("submit", function (ev) {
    ev.preventDefault();

    $(this).find("input").blur();

    let len = 0;
    for (let o in invalidFields) {
      len++;
    }

    if (len === 0) {
      // all ok
      invalidFormAlert.addClass("hidden");
    } else {
      invalidFormAlert.removeClass("hidden");
      return;
    }

    // add ajax field
    $('<input />').attr('type', 'hidden')
      .attr('name', "ajax").attr('value', "true")
      .appendTo(this);


    if (grecaptcha && typeof grecaptcha.execute == "function") {
      grecaptcha.execute();
    }
  });

  window.onSubmit = function (token) {

    submitFormButton.removeClass("btn-primary").attr("disabled", true);
    signForm.removeClass("btn-primary").attr("disabled", true);

    $('<input />').attr('type', 'hidden')
      .attr('name', "g-recaptcha-response").attr('value', token)
      .appendTo(form);


    $.ajax({
      url: ngoUrl,
      type: "POST",
      dataType: "json",
      data: form.serialize(),
      success: function (data) {
        if (data.url) {
          window.location = data.url;
        } else {
          message = errors["server_error"];
          submitFormButton.addClass("btn-primary").removeClass("btn-success").attr("disabled", false);
          signForm.addClass("btn-primary").removeClass("btn-success").attr("disabled", false);

          invalidFormAlert.removeClass("hidden").find("span").text(message);
          grecaptcha.reset();
        }
      },
      error: function (data) {

        if (grecaptcha && typeof grecaptcha.reset == "function") {
          grecaptcha.reset()
        }

        let response = data.responseJSON;
        let message;
        if (data.status === 500 || response.server) {
          message = errors["server_error"];
        } else if (response.fields && response.fields.length) {
          message = errors["fields_error"];

          for (let field in response.fields) {
            message += response.fields + ", ";
          }
          message = message.slice(0, -2);
        } else {
          message = errors["server_error"];
        }

        submitFormButton.addClass("btn-primary").removeClass("btn-success").attr("disabled", false);
        invalidFormAlert.removeClass("hidden").find("span").text(message);
      }
    });
  };

});
