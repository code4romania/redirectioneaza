import "@fontsource/inter/latin-ext-400.css";
import "@fontsource/inter/latin-ext-400-italic.css";
import "@fontsource/inter/latin-ext-500.css";
import "@fontsource/inter/latin-ext-500-italic.css";
import "@fontsource/inter/latin-ext-600.css";
import "@fontsource/inter/latin-ext-600-italic.css";
import "@fontsource/inter/latin-ext-800.css";
import "@fontsource/inter/latin-ext-800-italic.css";
import './main.css';
import 'tippy.js/dist/tippy.css';

import Alpine from 'alpinejs';
import collapse from '@alpinejs/collapse';
import focus from '@alpinejs/focus';
import Tooltip from '@ryangjchandler/alpine-tooltip';
import combobox from './combobox';
import select from './select';
import ngoSearch from './ngoSearch';
import signature from './signature';
import twoPercentForm from './twoPercentForm';
import imageUpload from './imageUpload';

Alpine.plugin(collapse);
Alpine.plugin(focus);
Alpine.plugin(Tooltip);

Alpine.data('combobox', combobox);
Alpine.data('select', select);
Alpine.data('ngoSearch', ngoSearch);
Alpine.data('signature', signature);
Alpine.data('twoPercentForm', twoPercentForm);
Alpine.data('imageUpload', imageUpload);

window.Alpine = Alpine;

Alpine.start();
