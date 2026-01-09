<template>
  <div class="attack-roster">
    <div class="title-with-tooltip">
      <h3 class="section-title">⚔️ Attack Roster</h3>
      <Tooltip text="Select which ships you have available. The heatmap will only show matchups you can execute." />
    </div>
    <p class="section-description">Select the ships you have available for attacking</p>
    
    <!-- Capital Ships Section -->
    <div class="roster-section">
      <div class="section-header">
        <h4>Capital Ships</h4>
        <div class="bulk-actions">
          <button @click="selectAllCapital" class="btn-small">Select All</button>
          <button @click="deselectAllCapital" class="btn-small">Deselect All</button>
        </div>
      </div>
      
      <div class="ship-grid">
        <div
          v-for="ship in capitalShips"
          :key="ship.id"
          class="ship-card"
          :class="{ selected: selectedCapitalShips.includes(ship.id) }"
          @click="toggleCapitalShip(ship.id)"
          @keydown.space.enter="toggleCapitalShip(ship.id)"
          role="button"
          :tabindex="0"
          :aria-label="`Select ${ship.name}`"
          :aria-pressed="selectedCapitalShips.includes(ship.id)"
        >
          <div class="ship-image-wrapper">
            <ShipImage
              :image-url="ship.image"
              :ship-name="ship.name"
              size="large"
            />
          </div>
          <span class="ship-name-overlay">{{ ship.name }}</span>
        </div>
      </div>
    </div>
    
    <!-- Regular Ships Section -->
    <div class="roster-section">
      <div class="section-header">
        <h4>Regular Ships</h4>
        <div class="bulk-actions">
          <button @click="selectAllRegular" class="btn-small">Select All</button>
          <button @click="deselectAllRegular" class="btn-small">Deselect All</button>
        </div>
      </div>

      <div v-for="(ships, faction) in regularShipsByFaction" :key="faction" class="faction-group">
        <div class="faction-header">
          <div class="faction-title">
            <h5>{{ faction }}</h5>
            <span class="ship-count">({{ ships.length }} ships)</span>
          </div>
          <div class="faction-actions">
            <button @click="selectFaction(faction)" class="faction-btn">Select All</button>
            <button @click="deselectFaction(faction)" class="faction-btn">Deselect All</button>
          </div>
        </div>
        <div class="ship-grid">
          <div
            v-for="ship in ships"
            :key="ship.name || ship"
            class="ship-card"
            :class="{ selected: selectedRegularShips.includes(ship.name || ship) }"
            @click="toggleRegularShip(ship.name || ship)"
            @keydown.space.enter="toggleRegularShip(ship.name || ship)"
            role="button"
            :tabindex="0"
            :aria-label="`Select ${ship.name || ship}`"
            :aria-pressed="selectedRegularShips.includes(ship.name || ship)"
          >
            <div class="ship-image-wrapper">
              <ShipImage
                v-if="ship.image"
                :image-url="ship.image"
                :ship-name="ship.name || ship"
                size="large"
              />
            </div>
            <span class="ship-name-overlay">{{ ship.name || ship }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import Tooltip from './Tooltip.vue'
import ShipImage from './ShipImage.vue'

export default {
  name: 'AttackRoster',
  components: {
    Tooltip,
    ShipImage
  },
  props: {
    capitalShips: {
      type: Array,
      required: true
    },
    regularShips: {
      type: Array,
      required: true
    },
    regularShipsByFaction: {
      type: Object,
      default: () => ({})
    },
    modelValue: {
      type: Object,
      default: () => ({ capitalShips: [], regularShips: [] })
    }
  },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const selectedCapitalShips = ref(props.modelValue.capitalShips || [])
    const selectedRegularShips = ref(props.modelValue.regularShips || [])

    const selectAllCapital = () => {
      selectedCapitalShips.value = props.capitalShips.map(ship => ship.id)
      onSelectionChange()
    }

    const deselectAllCapital = () => {
      selectedCapitalShips.value = []
      onSelectionChange()
    }

    const selectAllRegular = () => {
      selectedRegularShips.value = [...props.regularShips]
      onSelectionChange()
    }

    const deselectAllRegular = () => {
      selectedRegularShips.value = []
      onSelectionChange()
    }

    const selectFaction = (faction) => {
      const factionShips = props.regularShipsByFaction[faction] || []
      const newSelection = new Set(selectedRegularShips.value)
      factionShips.forEach(ship => {
        const shipName = ship.name || ship
        newSelection.add(shipName)
      })
      selectedRegularShips.value = Array.from(newSelection)
      onSelectionChange()
    }

    const deselectFaction = (faction) => {
      const factionShips = props.regularShipsByFaction[faction] || []
      const factionShipNames = new Set(factionShips.map(ship => ship.name || ship))
      selectedRegularShips.value = selectedRegularShips.value.filter(ship => !factionShipNames.has(ship))
      onSelectionChange()
    }

    const toggleCapitalShip = (shipId) => {
      const index = selectedCapitalShips.value.indexOf(shipId)
      if (index > -1) {
        selectedCapitalShips.value.splice(index, 1)
      } else {
        selectedCapitalShips.value.push(shipId)
      }
      onSelectionChange()
    }

    const toggleRegularShip = (shipName) => {
      const index = selectedRegularShips.value.indexOf(shipName)
      if (index > -1) {
        selectedRegularShips.value.splice(index, 1)
      } else {
        selectedRegularShips.value.push(shipName)
      }
      onSelectionChange()
    }

    const onSelectionChange = () => {
      emit('update:modelValue', {
        capitalShips: selectedCapitalShips.value,
        regularShips: selectedRegularShips.value
      })
    }

    // Watch for external changes
    watch(() => props.modelValue, (newValue) => {
      if (newValue) {
        selectedCapitalShips.value = newValue.capitalShips || []
        selectedRegularShips.value = newValue.regularShips || []
      }
    }, { deep: true })

    return {
      selectedCapitalShips,
      selectedRegularShips,
      selectAllCapital,
      deselectAllCapital,
      selectFaction,
      deselectFaction,
      selectAllRegular,
      deselectAllRegular,
      toggleCapitalShip,
      toggleRegularShip,
      onSelectionChange
    }
  }
}
</script>

<style scoped>
.attack-roster {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.title-with-tooltip {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.section-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.25rem;
}

.section-description {
  margin: 0 0 1.5rem 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.roster-section {
  margin-bottom: 2rem;
}

.faction-group {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--input-bg);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.faction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border-color);
}

.faction-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.faction-header h5 {
  margin: 0;
  color: var(--primary-color);
  font-size: 1rem;
  font-weight: 600;
}

.ship-count {
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-weight: normal;
}

.faction-actions {
  display: flex;
  gap: 0.5rem;
}

.faction-btn {
  padding: 0.35rem 0.7rem;
  background: var(--input-bg);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.faction-btn:hover {
  background: var(--hover-bg);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.roster-section:last-child {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid var(--border-color);
}

.section-header h4 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.1rem;
}

.bulk-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-small {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-small:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

.btn-small:active {
  transform: translateY(0);
}

.ship-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1rem;
}

.ship-card {
  position: relative;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s ease;
  border: 3px solid transparent;
  opacity: 0.7;
  transform: scale(1);
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ship-card:hover {
  opacity: 0.9;
  transform: scale(1.05);
  border-color: var(--primary-color);
}

.ship-card:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

.ship-card.selected {
  opacity: 1;
  border-color: var(--primary-color);
  box-shadow: 0 0 12px rgba(var(--primary-color-rgb), 0.4);
}

.ship-image-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.ship-name-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.9), transparent);
  color: white;
  padding: 0.5rem 0.5rem;
  text-align: center;
  font-size: 0.85rem;
  font-weight: 500;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
  user-select: none;
  word-break: break-word;
  line-height: 1.2;
}

@media (max-width: 768px) {
  .ship-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 0.75rem;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .faction-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .faction-actions {
    width: 100%;
  }

  .faction-btn {
    flex: 1;
  }

  .ship-card {
    border-width: 2px;
  }

  .ship-name-overlay {
    font-size: 0.75rem;
    padding: 0.35rem 0.35rem;
  }
}
</style>

