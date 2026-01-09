<template>
  <div class="season-selector">
    <div class="season-header">
      <h3>Select Seasons</h3>
      <button @click="toggleAll" class="toggle-all-btn">
        {{ allSelected ? 'Deselect All' : 'Select All' }}
      </button>
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
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      selectedSeasons: []
    }
  },
  computed: {
    allSelected() {
      return this.selectedSeasons.length === this.seasons.length && this.seasons.length > 0
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
  margin-bottom: 2rem;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

.season-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
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

.selected-info {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-style: italic;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}
</style>

