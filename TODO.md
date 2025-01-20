# Things to do to make the front-end work properly


## Donation form

### Pages

- no login necessary
- you need a valid NGO
- /<ngo-slug>/

### Files

- `templates/v2/form/redirection.html`
- `templates/v2/form/signature.html`

### Issues

  - [ ] Properly style the errors coming from BE
  - [ ] Set up captcha validation (set the `g-recaptcha-response` input, see `twopercent.js:183`)
    - make the captcha do its own work @tamariei
  - [ ] When clearing the signature, the empty `src` is displayed for the `<img>`
  - [ ] Resize the signature preview to fit the `<img>` container
  - [x] Mark the mandatory fields properly @idormenco
  - [x] Complete the flow (add a `success & download` page) @tamariei
  - [x] Add a button to close the modal @idormenco
  - [x] Checks need to be done before the button to open the modal is clicked or change the flow @idormenco
  - [x] Connect BE & FE for the donation form @tamarei
  - [x] Why is `x-trap.inert.noscroll="modalIsOpen"` displaying as a warning?
  - [x] Figure out how to disable the signature script on other pages @idormenco


## Login

### Files

- `templates/v2/socialaccount/login.html`
- `templates/v2/account/errors/login/**`

### Issues

  - [x] The user isn't redirected to Cognito for login
  - [ ] The error pages need to be styled properly @tamariei & @danniel


## Organization Data / NGO Profile

### Pages

- login as: NGO
- /organizatia-mea/prezentare/
- /organizatia-mea/formulare/

### Files

- `templates/v2/ngo-account/my-organization/*.html`

### Issues

  - [ ] The desktop sidebar isn't displayed properly
  - [ ] Check the data for changes when switching tabs
  - [ ] Max characters validation for description & other fields
  - [ ] The logo upload doesn't work properly
  - [x] Mark the mandatory fields properly @idormenco
  - [x] The disabled form fields need to be styled properly @idormenco
  - [x] Connect the form to the BE properly @tamariei
  - [x] The "save" & "get from NGO Hub" buttons should be styled the same @idormenco


## Organization's redirections

### Pages

- login as: NGO
- /organizatia-mea/redirectionari/

### Files

- `templates/v2/ngo-account/redirections/**`

### Issues

  - [ ] Django template: the `nr. crt./#` column from `list-header.html` & `list-items.html` should be calculated properly
  ~~The pagination doesn't show up properly (it should be right-aligned)~~  (fixed because we have the "items/page" element)
  - [x] Make the generate archive button work
  ~~Make the download table button work~~  (delayed because the feature requires a new BE feature)


## Organization's archives

### Pages

- login as: NGO
- /organizatia-mea/arhive/

### Files

- `templates/v2/ngo-account/archives/**`

### Issues

  - [ ] Align the table elements better (it's the same table as in the `redirections` page but with different columns)
  ~~Same issue with the pagination as in the `redirections` page~~  (fixed because we have the "items/page" element)


## Production-ready Dockerfile

### Files

- `docker/dockerfiles/Dockerfile.dev`

### Issues

  - [ ] NPM doesn't install packages properly and uses local packages instead @idormenco
