import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig({ plugins: [react(), tailwindcss()], server: { host: '127.0.0.1', watch: { usePolling: Boolean(process.env.WSL_DISTRO_NAME), interval: 500 }, proxy: { '/api': process.env.API_PROXY || 'http://127.0.0.1:8000' } } });
