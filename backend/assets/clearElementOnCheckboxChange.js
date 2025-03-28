export default function (elementId, alpineVariable, triggerValue, isRequired = false) {
  return {
    isRequired: null,
    element: null,
    triggerValue: null,
    clearElement() {
      this.element.value = '';
      this.element.required = false;
    },
    unclearElement() {
      this.element.required = this.isRequired;
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
