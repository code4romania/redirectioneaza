# Things to do to make the front-end work properly


## Dockerfile

### Files:

- `docker/dockerfiles/Dockerfile.dev`

### Issues:

  - [ ] NPM doesn't install packages properly and uses local packages instead


## Donation form

### Files:

- `templates/v2/form/donation.html`
- `templates/v2/form/signature.html`

### Issues:

  - [ ] Complete the flow (add a `success & download` page)
  - [ ] The modal doesn't disappear when clicked outside it
  - [ ] Checks need to be done before the button to open the modal is clicked
  - [ ] Connect BE & FE for the donation form
  - [ ] Why is `x-trap.inert.noscroll="modalIsOpen"` displaying as a warning?
  - [ ] Figure out how to disable the signature script on other pages


## Login

### Files:

- `templates/v2/socialaccount/login.html`
- `templates/v2/account/errors/login/**`

### Issues:

  - [ ] The user isn't redirected to Cognito for login
  - [ ] The error pages need to be styled properly


## Organization Data / NGO Profile

### Files:

- `templates/v2/ngo-account/my-organizations/**`

### Issues:

  - [ ] The disabled form fields need to be styled properly
  - [ ] Connect the form to the BE properly
  - [ ] Check the data for changes when switching tabs
  - [ ] The "save" & "get from NGO Hub" buttons should be styled the same
  - [ ] Max characters validation for description & other fields
  - [ ] The logo upload doesn't work properly


## Organization's redirections

### Files:

- `templates/v2/ngo-account/redirections/**`

### Issues:

  - [ ] The pagination doesn't show up properly (it should be right-aligned)
  - [ ] Django template: the `nr. crt./#` column from `list-header.html` & `list-items.html` should be calculated properly
  - [ ] Make the generate archive button work
  - [ ] Make the download table button work


## Organization's archives

### Files:

- `templates/v2/ngo-account/archives/**`

### Issues:

  - [ ] Same issue with the pagination as in the `redirections` page
  - [ ] Align the table elements better (it's the same table as in the `redirections` page but with different columns)