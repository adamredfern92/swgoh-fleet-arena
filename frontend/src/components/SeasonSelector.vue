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
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.season-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.season-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.toggle-all-btn {
  padding: 6px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.toggle-all-btn:hover {
  background: #0056b3;
}

.season-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
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
}

.season-checkbox input[type="checkbox"] {
  margin-right: 8px;
  cursor: pointer;
}

.season-label {
  font-size: 14px;
  color: #555;
}

.selected-info {
  font-size: 13px;
  color: #666;
  font-style: italic;
  padding-top: 8px;
  border-top: 1px solid #eee;
}
</style>

