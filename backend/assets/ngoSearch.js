export default function() {
  return {
    query: null,
    isOpen: false,
    results: [],

    open() {
      if (!this.results.length) {
        return;
      }

      this.isOpen = true;
    },

    close() {
      this.isOpen = false;
    },

    async search() {
      const url = new URL(window.location.origin + '/api/search');
      url.searchParams.set('q', this.query);

      this.results = await (await fetch(url)).json();

      this.open();
    },

    init() {
      this.$watch('query', () => this.search());
    }
  }
}
