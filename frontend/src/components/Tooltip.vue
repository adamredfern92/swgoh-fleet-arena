<template>
  <div class="tooltip-wrapper">
    <span class="tooltip-trigger">
      <slot></slot>
      <span class="info-icon">ⓘ</span>
    </span>
    <div class="tooltip-content">
      {{ text }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'Tooltip',
  props: {
    text: {
      type: String,
      required: true
    }
  }
}
</script>

<style scoped>
.tooltip-wrapper {
  position: relative;
  display: inline-block;
}

.tooltip-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  cursor: help;
}

.info-icon {
  font-size: 0.85rem;
  color: var(--primary-color);
  opacity: 0.7;
  transition: opacity 0.2s;
}

.tooltip-trigger:hover .info-icon {
  opacity: 1;
}

.tooltip-content {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: 8px;
  padding: 0.75rem 1rem;
  background: rgba(0, 0, 0, 0.95);
  color: white;
  border-radius: 6px;
  font-size: 0.85rem;
  line-height: 1.4;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s;
  pointer-events: none;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.tooltip-content::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(0, 0, 0, 0.95);
}

.tooltip-wrapper:hover .tooltip-content {
  opacity: 1;
  visibility: visible;
}

@media (max-width: 768px) {
  .tooltip-content {
    white-space: normal;
    max-width: 200px;
  }
}
</style>

