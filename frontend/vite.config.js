import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/campaigns': 'http://127.0.0.1:8000',
      '/content-entries': 'http://127.0.0.1:8000',
    },
  },
});
