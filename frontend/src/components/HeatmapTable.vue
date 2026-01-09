<template>
  <div class="heatmap-container">
    <h2 class="heatmap-title">Capital Ship Matchup Heatmap</h2>
    <p class="heatmap-subtitle">
      Click any cell to view detailed fleet composition and statistics
    </p>
    
    <div class="table-wrapper">
      <table class="heatmap-table">
        <thead>
          <tr>
            <th class="corner-cell">
              <div class="corner-labels">
                <span class="attacking-label">Attacking →</span>
                <span class="defending-label">↓ Defending</span>
              </div>
            </th>
            <th
              v-for="ship in attackingShipList"
              :key="'header-' + ship.id"
              class="ship-header"
            >
              <div class="ship-header-content">
                <ShipImage
                  :image-url="ship.image"
                  :ship-name="ship.name"
                  size="medium"
                />
                <div class="ship-name">{{ ship.name }}</div>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="defendingShip in shipList" :key="'row-' + defendingShip.id">
            <th class="ship-header row-header">
              <div class="ship-header-content">
                <ShipImage
                  :image-url="defendingShip.image"
                  :ship-name="defendingShip.name"
                  size="medium"
                />
                <div class="ship-name">{{ defendingShip.name }}</div>
              </div>
            </th>
            <td
              v-for="attackingShip in attackingShipList"
              :key="'cell-' + attackingShip.id + '-' + defendingShip.id"
              :class="getCellClass(attackingShip.id, defendingShip.id)"
              :style="getCellStyle(attackingShip.id, defendingShip.id)"
              @click="handleCellClick(attackingShip.id, defendingShip.id)"
              :title="getCellTooltip(attackingShip.id, defendingShip.id)"
            >
              <div class="cell-content">
                <span class="win-rate">{{ getCellValue(attackingShip.id, defendingShip.id) }}</span>
                <span class="battle-count">{{ getBattleCount(attackingShip.id, defendingShip.id) }}</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import ShipImage from './ShipImage.vue'

export default {
  name: 'HeatmapTable',
  components: {
    ShipImage
  },
  props: {
    matchupData: {
      type: Object,
      required: true
    },
    fleetConfig: {
      type: Object,
      default: () => ({ defense: [], attack: { capitalShips: [], regularShips: [] } })
    }
  },
  emits: ['cell-click'],
  setup(props, { emit }) {
    const shipList = computed(() => {
      if (!props.matchupData?.data) return []

      // Get unique ship IDs from the filtered data
      const defendingShips = new Set()
      const attackingShips = new Set()

      props.matchupData.data.forEach(row => {
        defendingShips.add(row.defending_ship_id)
        row.matchups.forEach(matchup => {
          attackingShips.add(matchup.attacking_ship_id)
        })
      })

      // Create ship list for defending (columns)
      const defendingList = Array.from(defendingShips).map(id => ({
        id,
        name: props.matchupData.ship_names?.[id] || id,
        image: props.matchupData.ship_images?.[id] || ''
      }))

      return defendingList
    })

    const attackingShipList = computed(() => {
      if (!props.matchupData?.data) return []

      const attackingShips = new Set()
      props.matchupData.data.forEach(row => {
        row.matchups.forEach(matchup => {
          attackingShips.add(matchup.attacking_ship_id)
        })
      })

      return Array.from(attackingShips).map(id => ({
        id,
        name: props.matchupData.ship_names?.[id] || id,
        image: props.matchupData.ship_images?.[id] || ''
      }))
    })

    const getMatchupData = (attackingId, defendingId) => {
      const row = props.matchupData?.data?.find(r => r.defending_ship_id === defendingId)
      if (!row) return null
      return row.matchups.find(m => m.attacking_ship_id === attackingId)
    }

    const getCellValue = (attackingId, defendingId) => {
      const matchup = getMatchupData(attackingId, defendingId)
      return matchup?.has_data ? matchup.win_rate_percent : 'N/A'
    }

    const getBattleCount = (attackingId, defendingId) => {
      const matchup = getMatchupData(attackingId, defendingId)
      return matchup?.has_data ? `(${matchup.battle_count})` : ''
    }

    const getCellClass = (attackingId, defendingId) => {
      const classes = ['heatmap-cell']
      const matchup = getMatchupData(attackingId, defendingId)

      if (matchup?.has_data) {
        classes.push('clickable')
        // Add mirror-match class for same ship matchups
        if (attackingId === defendingId) {
          classes.push('mirror-match')
        }
      } else {
        classes.push('no-data')
      }

      return classes.join(' ')
    }

    const getCellStyle = (attackingId, defendingId) => {
      const matchup = getMatchupData(attackingId, defendingId)

      // No data - show red background
      if (!matchup?.has_data) {
        return { backgroundColor: 'rgba(255, 50, 50, 0.3)' }
      }

      const winRate = matchup.win_rate
      // Color gradient from red (0%) to yellow (50%) to green (100%)
      let r, g, b
      if (winRate < 0.5) {
        // Red to Yellow
        r = 255
        g = Math.round(255 * (winRate / 0.5))
        b = 0
      } else {
        // Yellow to Green
        r = Math.round(255 * (1 - (winRate - 0.5) / 0.5))
        g = 255
        b = 0
      }

      const alpha = 0.3 + (winRate * 0.4) // Vary opacity based on win rate
      return { backgroundColor: `rgba(${r}, ${g}, ${b}, ${alpha})` }
    }

    const getCellTooltip = (attackingId, defendingId) => {
      const row = props.matchupData?.data?.find(r => r.defending_ship_id === defendingId)
      const matchup = row?.matchups.find(m => m.attacking_ship_id === attackingId)

      if (!matchup?.has_data) {
        return 'Insufficient data'
      }
      const isMirror = attackingId === defendingId
      const mirrorNote = isMirror ? ' (Mirror Match)' : ''
      return `${matchup.attacking_ship_name} vs ${row.defending_ship_name}${mirrorNote}\nWin Rate: ${matchup.win_rate_percent}\nBattles: ${matchup.battle_count}\nClick for details`
    }

    const handleCellClick = (attackingId, defendingId) => {
      const matchup = getMatchupData(attackingId, defendingId)
      if (matchup?.has_data) {
        emit('cell-click', attackingId, defendingId)
      }
    }

    return {
      shipList,
      attackingShipList,
      getCellValue,
      getBattleCount,
      getCellClass,
      getCellStyle,
      getCellTooltip,
      handleCellClick
    }
  }
}
</script>

<style scoped>
.table-wrapper {
  overflow-x: auto;
  margin-top: 20px;
}

.heatmap-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.corner-cell {
  background: rgba(102, 126, 234, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 15px;
  min-width: 120px;
  position: sticky;
  left: 0;
  z-index: 3;
}

.corner-labels {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-size: 0.75rem;
  color: #b0b0b0;
}

.ship-header {
  background: rgba(102, 126, 234, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12px 8px;
  font-weight: 500;
  color: #e0e0e0;
  text-align: center;
  min-width: 90px;
}

.ship-header-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.row-header .ship-header-content {
  flex-direction: row;
  justify-content: flex-start;
}

.row-header {
  position: sticky;
  left: 0;
  z-index: 2;
  text-align: left;
  padding-left: 15px;
}

.ship-name {
  white-space: nowrap;
}

.heatmap-cell {
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 10px;
  text-align: center;
  transition: all 0.2s ease;
  min-width: 90px;
  height: 70px;
}

.heatmap-cell.clickable {
  cursor: pointer;
}

.heatmap-cell.clickable:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  z-index: 1;
  border-color: #667eea;
}

.heatmap-cell.mirror-match {
  border: 2px solid rgba(255, 215, 0, 0.5);
}

.heatmap-cell.no-data {
  background: rgba(255, 50, 50, 0.3);
  cursor: not-allowed;
}

.heatmap-cell.no-data .win-rate {
  color: #ff6b6b;
  font-weight: 700;
}

.cell-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
  justify-content: center;
}

.win-rate {
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.battle-count {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.7);
}

@media (max-width: 768px) {
  .heatmap-table {
    font-size: 0.75rem;
  }

  .ship-header {
    min-width: 70px;
    padding: 8px 4px;
  }

  .heatmap-cell {
    min-width: 70px;
    height: 60px;
    padding: 6px;
  }

  .win-rate {
    font-size: 0.85rem;
  }

  .battle-count {
    font-size: 0.65rem;
  }
}
</style>

