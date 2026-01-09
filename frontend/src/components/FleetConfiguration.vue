<template>
  <div class="fleet-configuration">
    <div class="config-header">
      <h2>⚙️ Fleet Configuration</h2>
      <button @click="toggleCollapse" class="collapse-btn">
        {{ isCollapsed ? '▼ Expand' : '▲ Collapse' }}
      </button>
    </div>
    
    <div v-if="!isCollapsed" class="config-content">
      <!-- Defense Setup -->
      <DefenseSetup
        ref="defenseSetupRef"
        :capital-ships="capitalShips"
        @update="handleDefenseUpdate"
      />
      
      <!-- Attack Roster -->
      <AttackRoster
        :capital-ships="capitalShips"
        :regular-ships="regularShips"
        :regular-ships-by-faction="regularShipsByFaction"
        v-model="attackRoster"
      />
      
      <!-- Configuration Summary -->
      <div class="config-summary">
        <h4>📊 Current Configuration</h4>
        <div class="summary-content">
          <div class="summary-item">
            <strong>Defense:</strong>
            <span v-if="defenseShipNames.length > 0">
              {{ defenseShipNames.join(', ') }}
            </span>
            <span v-else class="empty">No defense configured</span>
          </div>
          <div class="summary-item">
            <strong>Attack:</strong>
            <span v-if="attackRoster.capitalShips.length > 0 || attackRoster.regularShips.length > 0">
              {{ attackRoster.capitalShips.length }} capital ships, 
              {{ attackRoster.regularShips.length }} regular ships
            </span>
            <span v-else class="empty">No attack roster configured</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import axios from 'axios'
import DefenseSetup from './DefenseSetup.vue'
import AttackRoster from './AttackRoster.vue'

export default {
  name: 'FleetConfiguration',
  components: {
    DefenseSetup,
    AttackRoster
  },
  emits: ['config-change'],
  setup(props, { emit }) {
    const isCollapsed = ref(false)
    const capitalShips = ref([])
    const regularShips = ref([])
    const regularShipsByFaction = ref({})
    const defenseConfig = ref([
      { capitalShip: '', startingShips: ['', '', ''], commonShips: [] },
      { capitalShip: '', startingShips: ['', '', ''], commonShips: [] },
      { capitalShip: '', startingShips: ['', '', ''], commonShips: [] }
    ])
    const attackRoster = ref({
      capitalShips: [],
      regularShips: []
    })

    const defenseShipNames = computed(() => {
      return defenseConfig.value
        .filter(slot => slot.capitalShip)
        .map(slot => {
          const ship = capitalShips.value.find(s => s.id === slot.capitalShip)
          return ship ? ship.name : slot.capitalShip
        })
    })

    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
      saveToLocalStorage()
    }

    const loadShipData = async () => {
      try {
        const response = await axios.get('/api/roster/all-ships')
        capitalShips.value = response.data.capital_ships
        regularShips.value = response.data.regular_ships
        regularShipsByFaction.value = response.data.regular_ships_by_faction || {}
      } catch (error) {
        console.error('Error loading ship data:', error)
      }
    }

    const saveToLocalStorage = () => {
      const config = {
        isCollapsed: isCollapsed.value,
        defenseConfig: defenseConfig.value,
        attackRoster: attackRoster.value
      }
      localStorage.setItem('fleetConfiguration', JSON.stringify(config))
    }

    const loadFromLocalStorage = () => {
      const saved = localStorage.getItem('fleetConfiguration')
      if (saved) {
        try {
          const config = JSON.parse(saved)
          isCollapsed.value = config.isCollapsed || false

          // Migrate old data: if startingShips contains ship names instead of IDs, clear them
          // Ship IDs are all uppercase (e.g., "RAVENSCLAW"), names have spaces/apostrophes
          if (config.defenseConfig) {
            config.defenseConfig = config.defenseConfig.map(slot => {
              const migratedSlot = { ...slot }
              // Check if any starting ship looks like a name (has space or apostrophe)
              if (slot.startingShips && slot.startingShips.some(ship => ship && (ship.includes(' ') || ship.includes("'")))) {
                console.log('Migrating old defense config with ship names to ship IDs')
                migratedSlot.startingShips = ['', '', '']
              }
              return migratedSlot
            })
          }

          defenseConfig.value = config.defenseConfig || defenseConfig.value
          attackRoster.value = config.attackRoster || attackRoster.value
        } catch (error) {
          console.error('Error loading saved configuration:', error)
        }
      } else {
        // First visit - initialize with all ships selected
        initializeDefaultAttackRoster()
      }
    }

    const initializeDefaultAttackRoster = () => {
      // Set all capital ships and regular ships as selected by default
      attackRoster.value = {
        capitalShips: capitalShips.value.map(ship => ship.id),
        regularShips: [...regularShips.value]
      }
    }

    const handleDefenseUpdate = (newDefenseConfig) => {
      defenseConfig.value = newDefenseConfig
      emitConfigChange()
    }

    const emitConfigChange = () => {
      emit('config-change', {
        defense: defenseConfig.value,
        attack: attackRoster.value
      })
      saveToLocalStorage()
    }

    // Only watch attackRoster, not defenseConfig (defense updates come through handleDefenseUpdate)
    watch(attackRoster, () => {
      emitConfigChange()
    }, { deep: true })

    const defenseSetupRef = ref(null)

    onMounted(async () => {
      await loadShipData()
      loadFromLocalStorage()

      // Initialize DefenseSetup with loaded config
      if (defenseSetupRef.value && defenseConfig.value.length > 0) {
        defenseSetupRef.value.initializeFromConfig(defenseConfig.value)
      }

      emitConfigChange()
    })

    return {
      isCollapsed,
      capitalShips,
      regularShips,
      regularShipsByFaction,
      defenseConfig,
      attackRoster,
      defenseShipNames,
      toggleCollapse,
      handleDefenseUpdate,
      defenseSetupRef
    }
  }
}
</script>

<style scoped>
.fleet-configuration {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.config-header h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.5rem;
}

.collapse-btn {
  padding: 0.5rem 1rem;
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.collapse-btn:hover {
  background: var(--hover-bg);
  border-color: var(--primary-color);
}

.config-content {
  animation: slideDown 0.3s ease-out;
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

.config-summary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  padding: 1.5rem;
  color: white;
}

.config-summary h4 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.summary-item {
  display: flex;
  gap: 0.5rem;
  font-size: 0.95rem;
}

.summary-item strong {
  min-width: 80px;
}

.summary-item .empty {
  opacity: 0.7;
  font-style: italic;
}

@media (max-width: 768px) {
  .config-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
}
</style>

