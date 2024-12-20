import "@fontsource/inter/latin-ext-400.css";
import "@fontsource/inter/latin-ext-400-italic.css";
import "@fontsource/inter/latin-ext-500.css";
import "@fontsource/inter/latin-ext-500-italic.css";
import "@fontsource/inter/latin-ext-600.css";
import "@fontsource/inter/latin-ext-600-italic.css";
import "@fontsource/inter/latin-ext-800.css";
import "@fontsource/inter/latin-ext-800-italic.css";
import './main.css';

import Alpine from 'alpinejs';
import collapse from '@alpinejs/collapse';
import ngoSearch from './ngoSearch';

Alpine.plugin(collapse);

Alpine.data('ngoSearch', ngoSearch);

window.Alpine = Alpine;

Alpine.start();
