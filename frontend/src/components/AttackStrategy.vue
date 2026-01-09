<template>
  <div v-if="defenseConfig.length > 0" class="attack-strategy">
    <div class="strategy-header">
      <h3 class="strategy-title">💡 Suggested Attack Strategy</h3>
      <div v-if="hasStrategy" class="strategy-summary">
        <span class="summary-label">Expected Wins:</span>
        <span class="summary-value" :class="getSummaryClass">{{ expectedWins }} / {{ totalDefenses }}</span>
      </div>
    </div>

    <div v-if="hasStrategy" class="strategy-content">
      <div v-for="(suggestion, index) in suggestions" :key="index" class="strategy-item">
        <div class="defense-target">
          <ShipImage
            v-if="shipImages[suggestion.defendingShip]"
            :image-url="shipImages[suggestion.defendingShip]"
            :ship-name="suggestion.defendingShip"
            size="small"
          />
          <strong>vs {{ suggestion.defendingShip }}</strong>
          <span v-if="suggestion.startingShips.length > 0" class="starting-ships">
            ({{ suggestion.startingShips.join(', ') }})
          </span>
        </div>
        <div class="attack-recommendation" :class="{ 'likely-loss': suggestion.isLoss }">
          <span class="arrow">→</span>
          <ShipImage
            v-if="shipImages[suggestion.attackingShip]"
            :image-url="shipImages[suggestion.attackingShip]"
            :ship-name="suggestion.attackingShip"
            size="small"
          />
          <span class="attacking-ship">{{ suggestion.attackingShip }}</span>
          <span class="win-rate" :class="getWinRateClass(suggestion.winRate)">
            {{ suggestion.winRatePercent }}
          </span>
          <span class="battle-count">({{ suggestion.battleCount }} battles)</span>
          <span v-if="suggestion.isLoss" class="loss-indicator">⚠️ Likely Loss</span>
        </div>
        <div v-if="suggestion.fleet" class="fleet-details">
          <div class="fleet-ships">
            <strong>Starting:</strong>
            <div class="ship-list">
              <div
                v-for="(ship, idx) in suggestion.fleet.starting_ships"
                :key="idx"
                class="ship-item-small"
              >
                <ShipImage
                  v-if="shipImages[ship]"
                  :image-url="shipImages[ship]"
                  :ship-name="ship"
                  size="small"
                />
                <span>{{ ship }}</span>
              </div>
            </div>
          </div>
          <div v-if="suggestion.fleet.reinforcements.length > 0" class="fleet-ships">
            <strong>Reinforcements:</strong>
            <div class="ship-list">
              <div
                v-for="(ship, idx) in suggestion.fleet.reinforcements"
                :key="idx"
                class="ship-item-small"
              >
                <ShipImage
                  v-if="shipImages[ship]"
                  :image-url="shipImages[ship]"
                  :ship-name="ship"
                  size="small"
                />
                <span>{{ ship }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="uncoveredDefenses.length > 0" class="uncovered-defenses">
        <p class="warning-text">⚠️ No available counter for:</p>
        <ul>
          <li v-for="defense in uncoveredDefenses" :key="defense">{{ defense }}</li>
        </ul>
        <p class="no-strategy-hint">
          All attacking ships have been assigned or no viable counters exist in your roster.
        </p>
      </div>
    </div>

    <div v-else class="no-strategy">
      <p>⚠️ No one-shot strategy available</p>
      <p class="no-strategy-hint">
        Try adjusting your attack roster or defense configuration to see available strategies.
      </p>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import ShipImage from './ShipImage.vue'

export default {
  name: 'AttackStrategy',
  components: {
    ShipImage
  },
  props: {
    matchupData: {
      type: Object,
      required: true
    },
    defenseConfig: {
      type: Array,
      default: () => []
    }
  },
  setup(props) {
    const suggestions = computed(() => {
      if (!props.matchupData?.data || props.defenseConfig.length === 0) {
        return []
      }

      const MIN_WIN_RATE = 0.20 // 20% threshold - below this is considered a loss

      // Build a list of defense slots with their matchup options
      const defenseSlots = props.defenseConfig
        .filter(slot => slot.capitalShip)
        .map(slot => {
          const defendingRow = props.matchupData.data.find(
            row => row.defending_ship_id === slot.capitalShip
          )

          if (!defendingRow || !defendingRow.matchups || defendingRow.matchups.length === 0) {
            return null
          }

          // Get all valid matchups (with data)
          const validMatchups = defendingRow.matchups
            .filter(matchup => matchup.has_data)
            .map(matchup => {
              // Map starting ship IDs to names
              const startingShipIds = slot.startingShips.filter(s => s)
              const startingShipNames = startingShipIds.map(shipId => {
                // Look up the ship name from the matchup data's ship_names
                return props.matchupData.ship_names?.[shipId] || shipId
              })

              return {
                ...matchup,
                defendingShip: defendingRow.defending_ship_name,
                defendingShipId: defendingRow.defending_ship_id,
                startingShips: startingShipNames
              }
            })

          return {
            slot,
            defendingRow,
            validMatchups
          }
        })
        .filter(item => item !== null)

      if (defenseSlots.length === 0) {
        return []
      }

      // Helper function to calculate score for an assignment
      // Score = number of wins (win_rate >= 20%) + sum of win rates for winning matchups
      const calculateScore = (assignment) => {
        let wins = 0
        let totalWinRate = 0

        assignment.forEach(matchup => {
          if (matchup && matchup.win_rate >= MIN_WIN_RATE) {
            wins++
            totalWinRate += matchup.win_rate
          }
        })

        // Prioritize number of wins, then total win rate
        return wins * 1000 + totalWinRate
      }

      // Generate all permutations and find the best assignment
      const findBestAssignment = (defenseIndex, usedAttackers, currentAssignment) => {
        // Base case: all defenses assigned
        if (defenseIndex >= defenseSlots.length) {
          return {
            assignment: [...currentAssignment],
            score: calculateScore(currentAssignment)
          }
        }

        const defenseSlot = defenseSlots[defenseIndex]
        let bestResult = {
          assignment: [],
          score: -Infinity
        }

        // Try each available attacking ship for this defense
        for (const matchup of defenseSlot.validMatchups) {
          if (!usedAttackers.has(matchup.attacking_ship_id)) {
            // Try this assignment
            usedAttackers.add(matchup.attacking_ship_id)
            currentAssignment.push(matchup)

            // Recurse to next defense
            const result = findBestAssignment(defenseIndex + 1, usedAttackers, currentAssignment)

            // Update best if this is better
            if (result.score > bestResult.score) {
              bestResult = result
            }

            // Backtrack
            currentAssignment.pop()
            usedAttackers.delete(matchup.attacking_ship_id)
          }
        }

        // Also try not assigning any attacker to this defense (if no good options)
        currentAssignment.push(null)
        const resultWithNull = findBestAssignment(defenseIndex + 1, usedAttackers, currentAssignment)
        if (resultWithNull.score > bestResult.score) {
          bestResult = resultWithNull
        }
        currentAssignment.pop()

        return bestResult
      }

      // Find the optimal assignment
      const bestResult = findBestAssignment(0, new Set(), [])

      // Convert to strategy format
      const strategies = bestResult.assignment
        .map((matchup, index) => {
          if (!matchup) return null

          return {
            defendingShip: matchup.defendingShip,
            startingShips: matchup.startingShips,
            attackingShip: matchup.attacking_ship_name,
            attackingShipId: matchup.attacking_ship_id,
            winRate: matchup.win_rate,
            winRatePercent: matchup.win_rate_percent,
            battleCount: matchup.battle_count,
            fleet: matchup.attacking_fleet,
            isLoss: matchup.win_rate < MIN_WIN_RATE
          }
        })
        .filter(s => s !== null)

      return strategies
    })

    const uncoveredDefenses = computed(() => {
      if (!props.matchupData?.data || props.defenseConfig.length === 0) {
        return []
      }

      // Get all configured defense ship names
      const configuredDefenses = props.defenseConfig
        .filter(slot => slot.capitalShip)
        .map(slot => {
          const row = props.matchupData.data.find(r => r.defending_ship_id === slot.capitalShip)
          return row ? row.defending_ship_name : null
        })
        .filter(name => name !== null)

      // Get defenses that have strategies
      const coveredDefenses = new Set(suggestions.value.map(s => s.defendingShip))

      // Return defenses without strategies
      return configuredDefenses.filter(defense => !coveredDefenses.has(defense))
    })

    const hasStrategy = computed(() => suggestions.value.length > 0)

    const expectedWins = computed(() => {
      return suggestions.value.filter(s => !s.isLoss).length
    })

    const totalDefenses = computed(() => {
      return props.defenseConfig.filter(slot => slot.capitalShip).length
    })

    const getSummaryClass = computed(() => {
      const ratio = expectedWins.value / totalDefenses.value
      if (ratio === 1) return 'perfect'
      if (ratio >= 0.67) return 'good'
      if (ratio >= 0.34) return 'moderate'
      return 'poor'
    })

    const getWinRateClass = (winRate) => {
      if (winRate >= 0.8) return 'excellent'
      if (winRate >= 0.6) return 'good'
      if (winRate >= 0.4) return 'moderate'
      return 'poor'
    }

    const shipImages = computed(() => {
      if (!props.matchupData) return {}

      const images = {}
      const shipNames = props.matchupData.ship_names || {}
      const shipImagesData = props.matchupData.ship_images || {}

      // Map ship names to their images
      Object.keys(shipNames).forEach(shipId => {
        const shipName = shipNames[shipId]
        const imageUrl = shipImagesData[shipId]
        if (shipName && imageUrl) {
          images[shipName] = imageUrl
        }
      })

      return images
    })

    return {
      suggestions,
      uncoveredDefenses,
      hasStrategy,
      expectedWins,
      totalDefenses,
      getSummaryClass,
      getWinRateClass,
      shipImages
    }
  }
}
</script>

<style scoped>
.attack-strategy {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
  border: 2px solid var(--primary-color);
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.strategy-title {
  margin: 0;
  color: var(--primary-color);
  font-size: 1.25rem;
}

.strategy-summary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--input-bg);
  border-radius: 6px;
}

.summary-label {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.summary-value {
  font-weight: bold;
  font-size: 1.1rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.summary-value.perfect {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.summary-value.good {
  background: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.summary-value.moderate {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.summary-value.poor {
  background: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.strategy-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.strategy-item {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 1rem;
}

.defense-target {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  color: var(--text-primary);
  font-size: 1rem;
}

.starting-ships {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-left: 0.5rem;
}

.attack-recommendation {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: var(--input-bg);
  border-radius: 4px;
}

.attack-recommendation.likely-loss {
  background: rgba(244, 67, 54, 0.1);
  border: 1px solid rgba(244, 67, 54, 0.3);
}

.loss-indicator {
  color: #f44336;
  font-weight: 600;
  font-size: 0.9rem;
}

.arrow {
  color: var(--primary-color);
  font-size: 1.2rem;
  font-weight: bold;
}

.attacking-ship {
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}

.win-rate {
  font-weight: bold;
  font-size: 1.1rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.win-rate.excellent {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.win-rate.good {
  background: rgba(33, 150, 243, 0.2);
  color: #2196f3;
}

.win-rate.moderate {
  background: rgba(255, 152, 0, 0.2);
  color: #ff9800;
}

.win-rate.poor {
  background: rgba(244, 67, 54, 0.2);
  color: #f44336;
}

.battle-count {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.fleet-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border-color);
}

.fleet-ships {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.fleet-ships strong {
  color: var(--text-primary);
}

.fleet-ships .ship-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.25rem;
}

.ship-item-small {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 0.85rem;
}

.uncovered-defenses {
  margin-top: 1rem;
  padding: 1rem;
  background: rgba(255, 152, 0, 0.1);
  border: 1px solid rgba(255, 152, 0, 0.3);
  border-radius: 6px;
}

.warning-text {
  color: #ff9800;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.uncovered-defenses ul {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
  color: var(--text-primary);
}

.uncovered-defenses li {
  margin: 0.25rem 0;
}

.no-strategy {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}

.no-strategy p:first-child {
  font-size: 1.1rem;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.no-strategy-hint {
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

@media (max-width: 768px) {
  .attack-recommendation {
    flex-wrap: wrap;
  }

  .attacking-ship {
    flex-basis: 100%;
  }
}
</style>

