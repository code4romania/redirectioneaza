export default function (elementId, alpineVariable, triggerValue) {
  return {
    init() {
      this[alpineVariable] = triggerValue;
      $watch(alpineVariable, value => {
        if (!value) {
          document.getElementById(elementId).value = triggerValue;
        }
      })
    },
  };
}
