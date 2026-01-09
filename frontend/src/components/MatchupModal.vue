<template>
  <div class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-content" @click.stop>
      <button class="close-button" @click="$emit('close')">&times;</button>
      
      <div class="modal-header">
        <h2>{{ matchup.attacking_ship }} vs {{ matchup.defending_ship }}</h2>
        <div class="matchup-stats">
          <div class="stat-item">
            <span class="stat-label">Win Rate:</span>
            <span class="stat-value" :class="getWinRateClass(matchup.win_rate)">
              {{ matchup.win_rate_percent }}
            </span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Battles:</span>
            <span class="stat-value">{{ matchup.battle_count }}</span>
          </div>
        </div>
      </div>

      <div class="modal-body">
        <div class="fleet-section">
          <h3 class="fleet-title attacking">⚔️ Attacking Fleet</h3>
          <div v-if="matchup.attacking_fleet" class="fleet-details">
            <div class="capital-ship">
              <strong>Capital Ship:</strong> {{ matchup.attacking_fleet.capital_ship }}
            </div>
            <div class="ship-group">
              <strong>Starting Ships:</strong>
              <ul class="ship-list">
                <li v-for="ship in matchup.attacking_fleet.starting_ships" :key="ship" class="ship-item">
                  <ShipImage
                    v-if="shipImages[ship]"
                    :image-url="shipImages[ship]"
                    :ship-name="ship"
                    size="small"
                  />
                  <span>{{ ship }}</span>
                </li>
              </ul>
            </div>
            <div class="ship-group" v-if="matchup.attacking_fleet.reinforcements?.length">
              <strong>Reinforcements:</strong>
              <ul class="ship-list">
                <li v-for="ship in matchup.attacking_fleet.reinforcements" :key="ship" class="ship-item">
                  <ShipImage
                    v-if="shipImages[ship]"
                    :image-url="shipImages[ship]"
                    :ship-name="ship"
                    size="small"
                  />
                  <span>{{ ship }}</span>
                </li>
              </ul>
            </div>
          </div>
          <div v-else class="no-data">No fleet data available</div>
        </div>

        <div class="vs-divider">VS</div>

        <div class="fleet-section">
          <h3 class="fleet-title defending">🛡️ Defending Fleet</h3>
          <div v-if="matchup.defending_fleet" class="fleet-details">
            <div class="capital-ship">
              <strong>Capital Ship:</strong> {{ matchup.defending_fleet.capital_ship }}
            </div>
            <div class="ship-group">
              <strong>Starting Ships:</strong>
              <ul class="ship-list">
                <li v-for="ship in matchup.defending_fleet.starting_ships" :key="ship" class="ship-item">
                  <ShipImage
                    v-if="shipImages[ship]"
                    :image-url="shipImages[ship]"
                    :ship-name="ship"
                    size="small"
                  />
                  <span>{{ ship }}</span>
                </li>
              </ul>
            </div>
            <div class="ship-group" v-if="matchup.defending_fleet.reinforcements?.length">
              <strong>Reinforcements:</strong>
              <ul class="ship-list">
                <li v-for="ship in matchup.defending_fleet.reinforcements" :key="ship" class="ship-item">
                  <ShipImage
                    v-if="shipImages[ship]"
                    :image-url="shipImages[ship]"
                    :ship-name="ship"
                    size="small"
                  />
                  <span>{{ ship }}</span>
                </li>
              </ul>
            </div>
          </div>
          <div v-else class="no-data">No fleet data available</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ShipImage from './ShipImage.vue'

export default {
  name: 'MatchupModal',
  components: {
    ShipImage
  },
  props: {
    matchup: {
      type: Object,
      required: true
    },
    shipImages: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['close'],
  methods: {
    handleOverlayClick() {
      this.$emit('close')
    },
    getWinRateClass(winRate) {
      if (winRate >= 0.75) return 'excellent'
      if (winRate >= 0.5) return 'good'
      if (winRate >= 0.25) return 'average'
      return 'poor'
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
  border-radius: 16px;
  max-width: 900px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  border: 2px solid rgba(102, 126, 234, 0.3);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.close-button {
  position: absolute;
  top: 15px;
  right: 15px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #fff;
  font-size: 2rem;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.close-button:hover {
  background: rgba(244, 67, 54, 0.8);
  transform: rotate(90deg);
}

.modal-header {
  padding: 30px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.3);
}

.modal-header h2 {
  color: #667eea;
  font-size: 1.8rem;
  margin-bottom: 20px;
}

.matchup-stats {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-label {
  color: #b0b0b0;
  font-size: 1rem;
}

.stat-value {
  font-size: 1.3rem;
  font-weight: 700;
  padding: 5px 15px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
}

.stat-value.excellent {
  color: #4caf50;
  background: rgba(76, 175, 80, 0.2);
}

.stat-value.good {
  color: #8bc34a;
  background: rgba(139, 195, 74, 0.2);
}

.stat-value.average {
  color: #ff9800;
  background: rgba(255, 152, 0, 0.2);
}

.stat-value.poor {
  color: #f44336;
  background: rgba(244, 67, 54, 0.2);
}

.modal-body {
  padding: 30px;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 30px;
  align-items: start;
}

.fleet-section {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 20px;
}

.fleet-title {
  font-size: 1.3rem;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.fleet-title.attacking {
  color: #ff6b6b;
}

.fleet-title.defending {
  color: #4dabf7;
}

.fleet-details {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.capital-ship {
  font-size: 1.1rem;
  color: #ffd700;
  padding: 10px;
  background: rgba(255, 215, 0, 0.1);
  border-radius: 6px;
  border-left: 3px solid #ffd700;
}

.ship-group {
  color: #e0e0e0;
}

.ship-group strong {
  display: block;
  margin-bottom: 8px;
  color: #b0b0b0;
  font-size: 0.9rem;
}

.ship-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ship-list li {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  border-left: 2px solid #667eea;
  font-size: 0.95rem;
}

.ship-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.vs-divider {
  font-size: 2rem;
  font-weight: 700;
  color: #667eea;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 0;
}

.no-data {
  color: #888;
  font-style: italic;
  text-align: center;
  padding: 20px;
}

@media (max-width: 768px) {
  .modal-content {
    max-height: 95vh;
  }

  .modal-header h2 {
    font-size: 1.3rem;
  }

  .modal-body {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .vs-divider {
    font-size: 1.5rem;
    padding: 10px 0;
  }

  .fleet-title {
    font-size: 1.1rem;
  }
}
</style>

