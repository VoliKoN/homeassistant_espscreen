<script setup lang="ts">
// One of the editor's own icons, as text in the icon font so it takes the colour and size of what it sits in. An icon
// that points a way (an arrow, a chevron, undo, the sidebar's edge) turns with a right-to-left page (styles/app.css,
// .ui-icon-dir), except inside what a screen draws, which stays left to right.
import { iconGlyph, type IconName } from "../../model/ui-icons";
const DIRECTIONAL = new Set<string>(["arrow-left", "arrow-right", "chevron-left", "chevron-right", "undo", "redo", "dock-left"]);
defineProps<{ name: IconName }>();
</script>

<template><span class="mdi ui-icon" :class="{ 'ui-icon-dir': DIRECTIONAL.has(name) }" aria-hidden="true">{{ iconGlyph(name) }}</span></template>
