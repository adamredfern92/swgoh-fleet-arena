<template>
  <div class="defense-setup">
    <div class="header-with-actions">
      <div class="title-with-tooltip">
        <h3 class="section-title">🛡️ Defense Configuration</h3>
        <Tooltip text="Select 3 capital ships for defense. The heatmap will only show matchups against these ships." />
      </div>
      <button @click="clearAll" class="clear-all-btn">Clear All</button>
    </div>
    <p class="section-description">Configure your 3 defensive fleets with capital ships and starting lineups</p>
    
    <div class="defense-slots">
      <div 
        v-for="(slot, index) in defenseSlots" 
        :key="index"
        class="defense-slot"
      >
        <div class="slot-header">
          <h4>Defense Slot {{ index + 1 }}</h4>
          <button
            @click="clearSlot(index)"
            class="clear-slot-btn"
            :disabled="!slot.capitalShip"
          >
            Clear
          </button>
        </div>
        
        <div class="slot-content">
          <!-- Capital Ship Selector -->
          <div class="form-group">
            <label :for="`capital-${index}`">Capital Ship:</label>
            <div class="ship-selector-with-image">
              <ShipImage
                v-if="slot.capitalShip"
                :image-url="getCapitalShipImage(slot.capitalShip)"
                :ship-name="getCapitalShipName(slot.capitalShip)"
                size="medium"
              />
              <select
                :id="`capital-${index}`"
                v-model="slot.capitalShip"
                @change="onCapitalShipChange(index)"
                class="capital-select"
              >
                <option value="">-- Select Capital Ship --</option>
                <option
                  v-for="ship in availableCapitalShips(index)"
                  :key="ship.id"
                  :value="ship.id"
                >
                  {{ ship.name }}
                </option>
              </select>
            </div>
          </div>
          
          <!-- Starting Ships Selectors -->
          <div v-if="slot.capitalShip" class="starting-ships">
            <label>Starting Ships:</label>
            <div class="ship-selectors">
              <div
                v-for="shipIndex in 3"
                :key="shipIndex"
                class="ship-selector-with-image"
              >
                <ShipImage
                  v-if="slot.startingShips[shipIndex - 1]"
                  :image-url="getStartingShipImage(index, shipIndex - 1)"
                  :ship-name="getStartingShipName(index, shipIndex - 1)"
                  size="small"
                />
                <select
                  v-model="slot.startingShips[shipIndex - 1]"
                  @change="onStartingShipChange(index)"
                  class="ship-select"
                >
                  <option value="">-- Select Ship {{ shipIndex }} --</option>
                  <option
                    v-for="ship in availableStartingShips(index, shipIndex - 1)"
                    :key="ship.ship_id"
                    :value="ship.ship_id"
                  >
                    {{ ship.ship_name }}
                  </option>
                </select>
              </div>
            </div>

            <!-- Display lineup info when all 3 starting ships are selected -->
            <div v-if="getLineupInfo(index)" class="lineup-info">
              <div class="lineup-info-header">
                <span class="info-icon">ℹ️</span>
                <strong>Most Common Reinforcements:</strong>
              </div>
              <div class="lineup-info-content">
                <div class="reinforcements">
                  <div
                    v-for="(shipName, idx) in getLineupInfo(index).reinforcementNames"
                    :key="idx"
                    class="reinforcement-item"
                  >
                    <ShipImage
                      :image-url="getReinforcementImage(shipName)"
                      :ship-name="shipName"
                      size="small"
                    />
                    <span>{{ shipName }}</span>
                  </div>
                  <span v-if="getLineupInfo(index).reinforcementNames.length === 0" class="no-reinforcements">
                    None
                  </span>
                </div>
                <div class="battle-count">
                  <span class="label">Total Battles:</span>
                  <span class="value">{{ getLineupInfo(index).totalBattles.toLocaleString() }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import Tooltip from './Tooltip.vue'
import ShipImage from './ShipImage.vue'

export default {
  name: 'DefenseSetup',
  components: {
    Tooltip,
    ShipImage
  },
  props: {
    capitalShips: {
      type: Array,
      required: true
    },
    initialConfig: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update'],
  setup(props, { emit }) {
    const defenseSlots = ref([
      { capitalShip: '', startingShips: ['', '', ''], commonShips: [] },
      { capitalShip: '', startingShips: ['', '', ''], commonShips: [] },
      { capitalShip: '', startingShips: ['', '', ''], commonShips: [] }
    ])

    const lineupInfos = ref([])

    // Method to initialize from config (called by parent after loading from localStorage)
    const initializeFromConfig = (config) => {
      if (config && config.length > 0) {
        config.forEach((slot, index) => {
          if (defenseSlots.value[index]) {
            defenseSlots.value[index] = { ...slot }
          }
        })
        // Fetch lineup info if any slots are complete
        fetchLineupInfo()
      }
    }

    const availableCapitalShips = (slotIndex) => {
      const selectedShips = defenseSlots.value
        .map((slot, idx) => idx !== slotIndex ? slot.capitalShip : null)
        .filter(ship => ship)
      
      return props.capitalShips.filter(ship => !selectedShips.includes(ship.id))
    }

    const availableStartingShips = (slotIndex, shipIndex) => {
      const slot = defenseSlots.value[slotIndex]
      const selectedShipIds = slot.startingShips.filter((ship, idx) => idx !== shipIndex && ship)

      return slot.commonShips.filter(ship => !selectedShipIds.includes(ship.ship_id))
    }

    const onCapitalShipChange = async (slotIndex) => {
      const slot = defenseSlots.value[slotIndex]
      const selectedCapitalShip = slot.capitalShip

      // Clear starting ships and common ships when capital ship changes
      slot.startingShips = ['', '', '']
      slot.commonShips = []

      // Fetch common ships for the selected capital ship
      if (selectedCapitalShip) {
        try {
          const response = await axios.get(`/api/roster/common-starting-ships/${selectedCapitalShip}?top_n=20`)
          slot.commonShips = response.data.common_starting_ships

          // Prefill starting ships with the top 3 most common ships
          if (slot.commonShips.length >= 3) {
            slot.startingShips = [
              slot.commonShips[0].ship_id,
              slot.commonShips[1].ship_id,
              slot.commonShips[2].ship_id
            ]
          } else if (slot.commonShips.length > 0) {
            // If less than 3 common ships, fill what we have
            for (let i = 0; i < slot.commonShips.length; i++) {
              slot.startingShips[i] = slot.commonShips[i].ship_id
            }
          }
        } catch (error) {
          console.error('Error fetching common starting ships:', error)
        }
      }

      // Emit update to parent
      emitUpdate()

      // Fetch lineup info if we prefilled all 3 starting ships
      if (slot.startingShips.filter(s => s).length === 3) {
        fetchLineupInfo()
      }
    }

    const onStartingShipChange = (slotIndex) => {
      // Emit update to parent
      emitUpdate()

      // Fetch lineup info if all 3 starting ships are selected
      fetchLineupInfo()
    }

    const emitUpdate = () => {
      const config = defenseSlots.value.map(slot => ({ ...slot }))
      console.log('DefenseSetup emitting update:', JSON.stringify(config, null, 2))
      emit('update', config)
    }

    const fetchLineupInfo = async () => {
      // Only fetch if we have at least one complete defense slot
      const completeSlots = defenseSlots.value.filter(slot =>
        slot.capitalShip && slot.startingShips.filter(s => s).length === 3
      )

      if (completeSlots.length === 0) {
        lineupInfos.value = []
        return
      }

      try {
        const requestData = {
          defenseConfig: defenseSlots.value.map(slot => ({
            capitalShip: slot.capitalShip,
            startingShips: slot.startingShips
          }))
        }

        const response = await axios.post('/api/defense-lineup-info', requestData)
        lineupInfos.value = response.data.lineups || []
      } catch (error) {
        console.error('Error fetching lineup info:', error)
        lineupInfos.value = []
      }
    }

    const getLineupInfo = (slotIndex) => {
      const slot = defenseSlots.value[slotIndex]
      if (!slot.capitalShip) return null
      return lineupInfos.value.find(info => info.capitalShip === slot.capitalShip)
    }

    const clearSlot = (slotIndex) => {
      defenseSlots.value[slotIndex] = {
        capitalShip: '',
        startingShips: ['', '', ''],
        commonShips: []
      }
      emitUpdate()
      fetchLineupInfo()
    }

    const clearAll = () => {
      defenseSlots.value = [
        { capitalShip: '', startingShips: ['', '', ''], commonShips: [] },
        { capitalShip: '', startingShips: ['', '', ''], commonShips: [] },
        { capitalShip: '', startingShips: ['', '', ''], commonShips: [] }
      ]
      emitUpdate()
      lineupInfos.value = []
    }

    const getCapitalShipImage = (shipId) => {
      const ship = props.capitalShips.find(s => s.id === shipId)
      return ship?.image || ''
    }

    const getCapitalShipName = (shipId) => {
      const ship = props.capitalShips.find(s => s.id === shipId)
      return ship?.name || shipId
    }

    const getStartingShipImage = (slotIndex, shipIndex) => {
      const slot = defenseSlots.value[slotIndex]
      const shipId = slot.startingShips[shipIndex]
      if (!shipId) return ''
      const ship = slot.commonShips.find(s => s.ship_id === shipId)
      return ship?.image || ''
    }

    const getStartingShipName = (slotIndex, shipIndex) => {
      const slot = defenseSlots.value[slotIndex]
      const shipId = slot.startingShips[shipIndex]
      if (!shipId) return ''
      const ship = slot.commonShips.find(s => s.ship_id === shipId)
      return ship?.ship_name || shipId
    }

    const getReinforcementImage = (shipName) => {
      const lineupInfo = lineupInfos.value.find(info =>
        info.reinforcementNames && info.reinforcementNames.includes(shipName)
      )
      if (!lineupInfo) return ''

      const index = lineupInfo.reinforcementNames.indexOf(shipName)
      return lineupInfo.reinforcementImages?.[index] || ''
    }

    // No watch needed - DefenseSetup owns its own state completely
    // Parent only provides initial config, no two-way binding

    return {
      defenseSlots,
      availableCapitalShips,
      availableStartingShips,
      onCapitalShipChange,
      onStartingShipChange,
      clearSlot,
      clearAll,
      getLineupInfo,
      initializeFromConfig,
      getCapitalShipImage,
      getCapitalShipName,
      getStartingShipImage,
      getStartingShipName,
      getReinforcementImage
    }
  }
}
</script>

<style scoped>
.defense-setup {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.header-with-actions {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.5rem;
}

.title-with-tooltip {
  display: flex;
  align-items: center;
  gap: 0.5rem;
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

.defense-slots {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
}

.defense-slot {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  overflow: hidden;
}

.slot-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.slot-header h4 {
  margin: 0;
  color: white;
  font-size: 1rem;
  font-weight: 600;
}

.slot-content {
  padding: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
  font-weight: 500;
  font-size: 0.9rem;
}

.ship-selector-with-image {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ship-selector-with-image select {
  flex: 1;
}

.capital-select,
.ship-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: border-color 0.2s;
}

.capital-select:hover,
.ship-select:hover {
  border-color: var(--primary-color);
}

.capital-select:focus,
.ship-select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

.starting-ships {
  margin-top: 1rem;
}

.starting-ships > label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
  font-weight: 500;
  font-size: 0.9rem;
}

.ship-selectors {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.clear-all-btn {
  padding: 0.5rem 1rem;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.2s;
}

.clear-all-btn:hover {
  background: #d32f2f;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(244, 67, 54, 0.3);
}

.clear-slot-btn {
  padding: 0.4rem 0.8rem;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.clear-slot-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.clear-slot-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.lineup-info {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 6px;
}

.lineup-info-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  color: var(--primary-color);
  font-size: 0.95rem;
}

.info-icon {
  font-size: 1.1rem;
}

.lineup-info-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.reinforcements {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  color: var(--text-primary);
  font-size: 0.9rem;
  padding: 0.5rem;
  background: var(--input-bg);
  border-radius: 4px;
}

.reinforcement-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.no-reinforcements {
  color: var(--text-secondary);
  font-style: italic;
}

.battle-count {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
}

.battle-count .label {
  color: var(--text-secondary);
}

.battle-count .value {
  color: var(--primary-color);
  font-weight: 600;
}

@media (max-width: 768px) {
  .defense-slots {
    grid-template-columns: 1fr;
  }

  .header-with-actions {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>

