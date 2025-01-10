# Things to do to make the front-end work properly

## Donation form

### Files:

- `templates/v2/form/donation.html`
- `templates/v2/form/signature.html`

### Issues:

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
