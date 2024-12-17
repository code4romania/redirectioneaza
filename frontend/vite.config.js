import { defineConfig, loadEnv } from 'vite';
import { resolve } from 'path';


export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [],
    root: resolve(__dirname, './src'),
    base: command === 'serve' ? '/static/' : '',
    server: {
      open: false,
      host: '0.0.0.0',
      port: env.DJANGO_VITE_DEV_SERVER_PORT || 3000,
      watch: command === 'serve' ? { usePolling: true, disableGlobbing: false } : null,
    },
    resolve: {
    //   alias: {
    //     '@': resolve(__dirname, './src'),
    //     '@components': resolve(__dirname, './src/components'),
    //     '@constants': resolve(__dirname, './src/constants'),
    //     '@hooks': resolve(__dirname, './src/hooks'),
    //   },
      extensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
    },
    build: {
      manifest: "manifest.json",
      emptyOutDir: true,
      assetsDir: '',
      target: 'es2015',
      modulePreload: false,
      outDir: resolve(__dirname, './dist'),
      rollupOptions: {
        // input: {
        //   main: resolve('./src/main.jsx'),
        // },
        // output: {
        //   chunkFileNames: undefined,
        // },
      },
    },
  };
});
