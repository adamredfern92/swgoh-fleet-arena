<template>
  <div id="app">
    <header class="header">
      <div class="header-content">
        <div class="header-title-section">
          <h1>⚔️ SWGOH Fleet Analysis Dashboard</h1>
          <p>Capital Ship Matchup Win Rates{{ selectedSeasonsText }}</p>
        </div>
        <div v-if="availableSeasons.length > 0" class="header-season-selector">
          <SeasonSelector
            v-model="selectedSeasons"
            :seasons="availableSeasons"
            :collapsible="true"
            :initially-collapsed="true"
            @update:modelValue="handleSeasonChange"
          />
        </div>
      </div>
    </header>

    <div v-if="loading" class="loading">
      Loading matchup data
    </div>

    <div v-else-if="error" class="error">
      <strong>Error:</strong> {{ error }}
    </div>

    <template v-else>
      <FleetConfiguration
        @config-change="handleConfigChange"
      />
      <Legend />
      <HeatmapTable
        :matchupData="filteredMatchupData"
        :fleetConfig="fleetConfig"
        @cell-click="handleCellClick"
      />
      <AttackStrategy
        :matchupData="filteredMatchupData"
        :defenseConfig="fleetConfig.defense"
      />
      <MatchupModal
        v-if="selectedMatchup"
        :matchup="selectedMatchup"
        :ship-images="shipImages"
        @close="selectedMatchup = null"
      />
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import HeatmapTable from './components/HeatmapTable.vue'
import Legend from './components/Legend.vue'
import MatchupModal from './components/MatchupModal.vue'
import FleetConfiguration from './components/FleetConfiguration.vue'
import AttackStrategy from './components/AttackStrategy.vue'
import SeasonSelector from './components/SeasonSelector.vue'

export default {
  name: 'App',
  components: {
    HeatmapTable,
    Legend,
    MatchupModal,
    FleetConfiguration,
    AttackStrategy,
    SeasonSelector
  },
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const matchupData = ref(null)
    const selectedMatchup = ref(null)
    const availableSeasons = ref([])
    const selectedSeasons = ref([])
    const fleetConfig = ref({
      defense: [],
      attack: { capitalShips: [], regularShips: [] }
    })

    const selectedSeasonsText = computed(() => {
      if (selectedSeasons.value.length === 0) {
        return ''
      }
      if (selectedSeasons.value.length === availableSeasons.value.length) {
        return ' - All Seasons'
      }
      const seasonNumbers = selectedSeasons.value
        .map(id => {
          const season = availableSeasons.value.find(s => s.id === id)
          return season ? season.number : null
        })
        .filter(n => n !== null)
        .sort((a, b) => a - b)

      if (seasonNumbers.length === 1) {
        return ` - Season ${seasonNumbers[0]}`
      }
      return ` - Seasons ${seasonNumbers.join(', ')}`
    })

    const fetchMatchupData = async (showLoading = false) => {
      try {
        // Only show loading spinner on initial load, not on config updates
        if (showLoading) {
          loading.value = true
        }
        error.value = null

        console.log('fetchMatchupData called')
        console.log('Current fleetConfig.defense:', JSON.stringify(fleetConfig.value.defense, null, 2))
        console.log('Selected seasons:', selectedSeasons.value)

        // Check if we have defense configuration with starting ships
        const defenseWithStartingShips = fleetConfig.value.defense.filter(
          slot => slot.capitalShip && slot.startingShips && slot.startingShips.some(s => s)
        )

        console.log('Defense slots with starting ships:', defenseWithStartingShips.length)

        if (defenseWithStartingShips.length > 0) {
          // Use filtered endpoint when defense starting ships are configured
          console.log('Fetching filtered matchup data with defense config:', defenseWithStartingShips)
          const response = await axios.post('/api/matchup-matrix/filtered', {
            defenseConfig: defenseWithStartingShips,
            seasons: selectedSeasons.value.length > 0 ? selectedSeasons.value : null
          })
          matchupData.value = response.data
        } else {
          // Use regular endpoint when no defense starting ships configured
          console.log('Fetching regular matchup data (no starting ships configured)')
          const seasonsParam = selectedSeasons.value.length > 0 ? selectedSeasons.value.join(',') : null
          const response = await axios.get('/api/matchup-matrix', {
            params: seasonsParam ? { seasons: seasonsParam } : {}
          })
          matchupData.value = response.data
        }

      } catch (err) {
        console.error('Error fetching matchup data:', err)
        error.value = err.response?.data?.detail || err.message || 'Failed to load matchup data'
      } finally {
        if (showLoading) {
          loading.value = false
        }
      }
    }

    const fetchSeasons = async () => {
      try {
        const response = await axios.get('/api/seasons')
        availableSeasons.value = response.data.seasons
        // Select all seasons by default
        selectedSeasons.value = availableSeasons.value.map(s => s.id)
      } catch (err) {
        console.error('Error fetching seasons:', err)
        error.value = 'Failed to load available seasons'
      }
    }

    const handleSeasonChange = (newSeasons) => {
      selectedSeasons.value = newSeasons
      fetchMatchupData(false)
    }

    const handleCellClick = async (attackingId, defendingId) => {
      try {
        // First, try to get the matchup from the current matchupData (which may be filtered)
        const row = matchupData.value?.data?.find(r => r.defending_ship_id === defendingId)
        const matchup = row?.matchups?.find(m => m.attacking_ship_id === attackingId)

        // If we have fleet data in the matchup (from filtered endpoint), use it directly
        if (matchup && matchup.attacking_fleet && matchup.defending_fleet) {
          selectedMatchup.value = {
            attacking_ship: matchup.attacking_ship_name,
            defending_ship: row.defending_ship_name,
            win_rate: matchup.win_rate,
            win_rate_percent: matchup.win_rate_percent,
            battle_count: matchup.battle_count,
            attacking_fleet: matchup.attacking_fleet,
            defending_fleet: matchup.defending_fleet
          }
        } else {
          // Fall back to fetching from the detail endpoint (for unfiltered data)
          const response = await axios.get(`/api/matchup/${attackingId}/${defendingId}`)
          selectedMatchup.value = response.data
        }
      } catch (err) {
        console.error('Error fetching matchup details:', err)
        error.value = 'Failed to load matchup details'
      }
    }

    // Store the last defense key to detect changes
    const lastDefenseKey = ref('')

    const handleConfigChange = (config) => {
      // Extract only the relevant parts for comparison (capital ship and starting ships)
      const getDefenseKey = (defense) => {
        return defense.map(slot => ({
          capitalShip: slot.capitalShip,
          startingShips: slot.startingShips ? [...slot.startingShips] : []
        }))
      }

      const newDefenseKey = JSON.stringify(getDefenseKey(config.defense))
      fleetConfig.value = config

      // Only refetch if defense capital ship or starting ships changed
      // (ignore changes to commonShips array or attack roster)
      if (lastDefenseKey.value !== newDefenseKey) {
        lastDefenseKey.value = newDefenseKey
        fetchMatchupData()
      }
    }

    const filteredMatchupData = computed(() => {
      if (!matchupData.value) return null

      const defenseShipIds = fleetConfig.value.defense
        .filter(slot => slot.capitalShip)
        .map(slot => slot.capitalShip)

      const attackCapitalShips = fleetConfig.value.attack.capitalShips
      const attackRegularShips = new Set(fleetConfig.value.attack.regularShips)

      // If no configuration, return all data
      if (defenseShipIds.length === 0 && attackCapitalShips.length === 0) {
        return matchupData.value
      }

      // Helper function to check if attack has all required ships
      const hasAllAttackShips = (attackingFleet) => {
        if (!attackingFleet) return false
        if (attackRegularShips.size === 0) return true // No filter, show all

        const allShips = [
          ...(attackingFleet.starting_ships || []),
          ...(attackingFleet.reinforcements || [])
        ]

        // Check if all ships in the attacking fleet are available in the roster
        return allShips.every(ship => attackRegularShips.has(ship))
      }

      // Filter the data
      const filteredData = {
        ...matchupData.value,
        data: matchupData.value.data
          .filter(row => {
            // Filter defending ships by capital ship
            if (defenseShipIds.length > 0) {
              return defenseShipIds.includes(row.defending_ship_id)
            }
            return true
          })
          .map(row => {
            // Find the defense config for this defending ship
            const defenseSlot = fleetConfig.value.defense.find(
              slot => slot.capitalShip === row.defending_ship_id
            )

            return {
              ...row,
              matchups: row.matchups
                .filter(matchup => {
                  // Filter attacking capital ships
                  if (attackCapitalShips.length > 0) {
                    if (!attackCapitalShips.includes(matchup.attacking_ship_id)) {
                      return false
                    }
                  }

                  // Filter by attack ship availability
                  if (attackRegularShips.size > 0 && matchup.attacking_fleet) {
                    if (!hasAllAttackShips(matchup.attacking_fleet)) {
                      return false
                    }
                  }

                  return true
                })
            }
          })
      }

      return filteredData
    })

    const shipImages = computed(() => {
      // Create a mapping of ship names to image URLs from matchupData
      if (!matchupData.value) return {}

      const images = {}
      const shipNames = matchupData.value.ship_names || {}
      const shipImagesData = matchupData.value.ship_images || {}

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

    onMounted(async () => {
      await fetchSeasons()
      fetchMatchupData(true) // Show loading spinner on initial load
    })

    return {
      loading,
      error,
      matchupData,
      filteredMatchupData,
      selectedMatchup,
      fleetConfig,
      availableSeasons,
      selectedSeasons,
      selectedSeasonsText,
      shipImages,
      handleCellClick,
      handleConfigChange,
      handleSeasonChange
    }
  }
}
</script>

