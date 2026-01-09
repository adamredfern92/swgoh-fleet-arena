<template>
  <div class="season-selector" :class="{ 'is-collapsed': isCollapsed && isCollapsible }">
    <!-- Collapsed state: compact button showing selected seasons -->
    <button
      v-if="isCollapsible && isCollapsed"
      @click="toggleCollapse"
      class="season-toggle-btn"
      :title="selectedSeasonsCompactText"
    >
      <span class="season-icon">⚙️</span>
      <span class="season-compact-text">{{ selectedSeasonsCompactText }}</span>
      <span class="season-chevron">▼</span>
    </button>

    <!-- Expanded state: full season selector -->
    <div v-if="!isCollapsible || !isCollapsed" class="season-selector-expanded">
      <div class="season-header">
        <h3>Select Seasons</h3>
        <div class="season-header-actions">
          <button @click="toggleAll" class="toggle-all-btn">
            {{ allSelected ? 'Deselect All' : 'Select All' }}
          </button>
          <button
            v-if="isCollapsible"
            @click="toggleCollapse"
            class="collapse-btn"
            title="Collapse season selector"
          >
            ▲
          </button>
        </div>
      </div>

      <div class="season-list">
        <div
          v-for="season in seasons"
          :key="season.id"
          class="season-item"
        >
          <label class="season-checkbox">
            <input
              type="checkbox"
              :value="season.id"
              v-model="selectedSeasons"
              @change="handleChange"
            />
            <span class="season-label">{{ season.display_name }}</span>
          </label>
        </div>
      </div>

      <div v-if="selectedSeasons.length > 0" class="selected-info">
        Selected: {{ selectedSeasons.length }} of {{ seasons.length }} seasons
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SeasonSelector',
  props: {
    seasons: {
      type: Array,
      required: true,
      default: () => []
    },
    modelValue: {
      type: Array,
      default: () => []
    },
    collapsible: {
      type: Boolean,
      default: false
    },
    initiallyCollapsed: {
      type: Boolean,
      default: true
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      selectedSeasons: [],
      isCollapsed: this.initiallyCollapsed
    }
  },
  computed: {
    isCollapsible() {
      return this.collapsible
    },
    allSelected() {
      return this.selectedSeasons.length === this.seasons.length && this.seasons.length > 0
    },
    selectedSeasonsCompactText() {
      if (this.selectedSeasons.length === 0) {
        return 'No seasons selected'
      }
      if (this.selectedSeasons.length === this.seasons.length) {
        return 'All seasons'
      }

      // Get season numbers for selected seasons
      const seasonNumbers = this.selectedSeasons
        .map(id => {
          const season = this.seasons.find(s => s.id === id)
          return season ? season.number : null
        })
        .filter(n => n !== null)
        .sort((a, b) => a - b)

      if (seasonNumbers.length === 1) {
        return `Season ${seasonNumbers[0]}`
      }

      // Show first few seasons and count if more
      if (seasonNumbers.length <= 3) {
        return `Seasons ${seasonNumbers.join(', ')}`
      }

      return `${seasonNumbers.length} seasons`
    }
  },
  watch: {
    modelValue: {
      immediate: true,
      handler(newValue) {
        this.selectedSeasons = newValue || []
      }
    },
    seasons: {
      immediate: true,
      handler(newSeasons) {
        // If no seasons selected yet, select all by default
        if (this.selectedSeasons.length === 0 && newSeasons.length > 0) {
          this.selectedSeasons = newSeasons.map(s => s.id)
          this.$emit('update:modelValue', this.selectedSeasons)
        }
      }
    }
  },
  methods: {
    handleChange() {
      this.$emit('update:modelValue', this.selectedSeasons)
    },
    toggleAll() {
      if (this.allSelected) {
        this.selectedSeasons = []
      } else {
        this.selectedSeasons = this.seasons.map(s => s.id)
      }
      this.$emit('update:modelValue', this.selectedSeasons)
    },
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed
    }
  }
}
</script>

<style scoped>
.season-selector {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-season-selector .season-selector {
  padding: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

/* Collapsed state styles */
.season-selector.is-collapsed {
  padding: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

.season-toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  background: rgba(102, 126, 234, 0.15);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 8px;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.season-toggle-btn:hover {
  background: rgba(102, 126, 234, 0.25);
  border-color: rgba(102, 126, 234, 0.5);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.season-icon {
  font-size: 1rem;
}

.season-compact-text {
  flex: 1;
  text-align: left;
}

.season-chevron {
  font-size: 0.7rem;
  transition: transform 0.2s ease;
}

.season-toggle-btn:hover .season-chevron {
  transform: translateY(2px);
}

/* Expanded state styles */
.season-selector-expanded {
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.season-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.season-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.header-season-selector .season-header h3 {
  font-size: 1rem;
}

.season-header-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.toggle-all-btn {
  padding: 0.5rem 1rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
}

.toggle-all-btn:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.header-season-selector .toggle-all-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.8rem;
}

.collapse-btn {
  padding: 0.4rem 0.6rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.season-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.header-season-selector .season-list {
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.season-item {
  display: flex;
  align-items: center;
}

.season-checkbox {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
  padding: 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.season-checkbox:hover {
  background: var(--hover-bg);
}

.season-checkbox input[type="checkbox"] {
  margin-right: 0.5rem;
  cursor: pointer;
  width: 16px;
  height: 16px;
  accent-color: var(--primary-color);
}

.season-label {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.header-season-selector .season-label {
  font-size: 0.85rem;
}

.selected-info {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-style: italic;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.header-season-selector .selected-info {
  font-size: 0.75rem;
  padding-top: 0.5rem;
}

/* Header-specific expanded styles */
.header-season-selector .season-selector-expanded {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 8px;
  padding: 1rem;
  backdrop-filter: blur(10px);
}
</style>

