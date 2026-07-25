// wtl-dllm · ui/vite.config.ts
// what: vite build config
// by:   <wtl> watchthelight
// tags: ui, config

import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
})

