# Things to do to make the front-end work properly


## Donation form

### Pages

- no login necessary
- you need a valid NGO
- /<ngo-slug>/

### Files

- `templates/v2/form/donation.html`
- `templates/v2/form/signature.html`

### Issues

  - [x] Mark the mandatory fields properly @idormenco
  - [ ] Set up captcha validation (set the `g-recaptcha-response` input, see `twopercent.js:183`)
    - make the captcha do its own work @tamariei
  - [ ] Complete the flow (add a `success & download` page) @tamariei
  - [ ] Add a button to close the modal @idormenco
  - [ ] Checks need to be done before the button to open the modal is clicked or change the flow @idormenco
  - [ ] Connect BE & FE for the donation form @tamarei
  - [x] Why is `x-trap.inert.noscroll="modalIsOpen"` displaying as a warning?
  - [ ] Figure out how to disable the signature script on other pages @idormenco


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

  - [x] Mark the mandatory fields properly @idormenco
  - [x] The disabled form fields need to be styled properly @idormenco
  - [ ] Connect the form to the BE properly @tamariei
  - [ ] Check the data for changes when switching tabs
  - [x] The "save" & "get from NGO Hub" buttons should be styled the same @idormenco
  - [ ] Max characters validation for description & other fields
  - [ ] The logo upload doesn't work properly


## Organization's redirections

### Pages

- login as: NGO
- /organizatia-mea/redirectionari/

### Files

- `templates/v2/ngo-account/redirections/**`

### Issues

  ~~The pagination doesn't show up properly (it should be right-aligned)~~  (fixed because we have the "items/page" element)
  - [ ] Django template: the `nr. crt./#` column from `list-header.html` & `list-items.html` should be calculated properly
  - [x] Make the generate archive button work
  ~~Make the download table button work~~  (delayed because the feature requires a new BE feature)


## Organization's archives

### Pages

- login as: NGO
- /organizatia-mea/arhive/

### Files

- `templates/v2/ngo-account/archives/**`

### Issues

  ~~Same issue with the pagination as in the `redirections` page~~  (fixed because we have the "items/page" element)
  - [ ] Align the table elements better (it's the same table as in the `redirections` page but with different columns)


## Production-ready Dockerfile

### Files

- `docker/dockerfiles/Dockerfile.dev`

### Issues

  - [ ] NPM doesn't install packages properly and uses local packages instead @idormenco
