// wtl-dllm · ui/src/main.ts
// what: entry — fonts, global css, mount
// by:   <wtl> watchthelight
// tags: ui, entry

import "@fontsource-variable/figtree";
import "@fontsource/space-mono/400.css";
import "@fontsource/space-mono/700.css";
import "./app.css";
import { mount } from "svelte";
import App from "./App.svelte";

const app = mount(App, {
  target: document.getElementById("app")!,
});

export default app;
