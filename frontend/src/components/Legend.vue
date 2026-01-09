<template>
  <div class="legend">
    <h3>📊 How to Read the Heatmap</h3>
    <div class="legend-content">
      <div class="legend-section">
        <h4>Color Coding:</h4>
        <div class="legend-items">
          <div class="legend-item">
            <div class="legend-color" style="background: rgba(255, 0, 0, 0.5);"></div>
            <span class="legend-label">0-25% Win Rate (Poor)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: rgba(255, 128, 0, 0.5);"></div>
            <span class="legend-label">25-50% Win Rate (Below Average)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: rgba(255, 255, 0, 0.5);"></div>
            <span class="legend-label">50-75% Win Rate (Good)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: rgba(128, 255, 0, 0.5);"></div>
            <span class="legend-label">75-100% Win Rate (Excellent)</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background: rgba(100, 100, 100, 0.2);"></div>
            <span class="legend-label">No Data Available</span>
          </div>
        </div>
      </div>
      
      <div class="legend-section">
        <h4>Methodology:</h4>
        <ul class="methodology-list">
          <li>Each cell shows the <strong>best win rate</strong> for the attacking ship vs defending ship</li>
          <li>Data is filtered to show only matchups with <strong>10+ battles</strong> for statistical significance</li>
          <li>Numbers in parentheses show the <strong>battle count</strong> for that matchup</li>
          <li><strong>Click any cell</strong> to view detailed fleet compositions and statistics</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Legend'
}
</script>

<style scoped>
.legend-content {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.legend-section h4 {
  color: #b0b0b0;
  font-size: 1rem;
  margin-bottom: 12px;
  font-weight: 500;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.legend-color {
  width: 50px;
  height: 30px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.legend-label {
  font-size: 0.9rem;
  color: #d0d0d0;
}

.methodology-list {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.methodology-list li {
  padding-left: 25px;
  position: relative;
  color: #d0d0d0;
  line-height: 1.6;
}

.methodology-list li::before {
  content: '→';
  position: absolute;
  left: 0;
  color: #667eea;
  font-weight: bold;
}

.methodology-list strong {
  color: #fff;
}

@media (max-width: 768px) {
  .legend-items {
    flex-direction: column;
    gap: 12px;
  }
  
  .methodology-list {
    gap: 8px;
  }
  
  .methodology-list li {
    font-size: 0.9rem;
  }
}
</style>

