export default function (elementId, alpineVariable, triggerValue, isRequired = false) {
  return {
    isRequired: null,
    element: null,
    triggerValue: null,
    removeElementValue(element) {
      if (element.type === 'checkbox' || element.type === 'radio') {
        element.checked = false;
      } else if (element.type !== undefined) {
        element.value = '';
      } else {
        let descendentInputs = element.getElementsByTagName('input');
        if (descendentInputs.length === 0) return;
        for (let i = 0; i < descendentInputs.length; i++) {
          this.clearElement(descendentInputs[i]);
        }
      }
    },
    clearElement(element = null) {
      if (element === null) {
        element = this.element;
      }

      this.removeElementValue(element);
      element.required = false;
    },
    unclearElement(element = null) {
      if (element === null) {
        element = this.element;
      }
      element.required = this.isRequired;
    },
    setAlpineVariableDefault(alpineVariable) {
      let defaultValue = !this.triggerValue;
      if (!this.element.value) {
        defaultValue = this.triggerValue;
        this.clearElement();
      }
      this[alpineVariable] = defaultValue;
    },
    setAlpineVariableWatch(alpineVariable) {
      this.$watch(alpineVariable, value => {
        if (value === this.triggerValue) {
          this.clearElement();
        } else {
          this.unclearElement();
        }
      })
    },
    init() {
      this.isRequired = isRequired;
      this.element = document.getElementById(elementId);
      this.triggerValue = triggerValue;
      this.setAlpineVariableDefault(alpineVariable);
      this.setAlpineVariableWatch(alpineVariable);
    },
  };
}
