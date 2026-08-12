import { defineConfig } from 'vite';
import { resolve } from 'node:path';

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        index: resolve(import.meta.dirname, 'index.html'),
        catalog: resolve(import.meta.dirname, 'catalog.html'),
        preset: resolve(import.meta.dirname, 'preset.html'),
        custom: resolve(import.meta.dirname, 'custom.html'),
      },
    },
  },
});
