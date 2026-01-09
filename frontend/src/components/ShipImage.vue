<template>
  <div class="ship-image-container" :class="sizeClass">
    <img
      v-if="imageUrl && !imageError"
      :src="imageUrl"
      :alt="shipName"
      :title="shipName"
      class="ship-image"
      @error="handleImageError"
      loading="lazy"
    />
    <div v-else class="ship-image-placeholder" :title="shipName">
      <span class="ship-initial">{{ shipInitial }}</span>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'ShipImage',
  props: {
    imageUrl: {
      type: String,
      default: ''
    },
    shipName: {
      type: String,
      required: true
    },
    size: {
      type: String,
      default: 'medium', // small, medium, large
      validator: (value) => ['small', 'medium', 'large', 'xlarge'].includes(value)
    }
  },
  setup(props) {
    const imageError = ref(false)

    const handleImageError = () => {
      imageError.value = true
    }

    const shipInitial = computed(() => {
      return props.shipName ? props.shipName.charAt(0).toUpperCase() : '?'
    })

    const sizeClass = computed(() => `size-${props.size}`)

    return {
      imageError,
      handleImageError,
      shipInitial,
      sizeClass
    }
  }
}
</script>

<style scoped>
.ship-image-container {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  overflow: hidden;
  background: var(--bg-secondary);
  flex-shrink: 0;
}

.ship-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.ship-image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
  color: var(--text-secondary);
  font-weight: 600;
}

/* Size variants */
.size-small {
  width: 48px;
  height: 48px;
}

.size-small .ship-initial {
  font-size: 24px;
}

.size-medium {
  width: 64px;
  height: 64px;
}

.size-medium .ship-initial {
  font-size: 28px;
}

.size-large {
  width: 96px;
  height: 96px;
}

.size-large .ship-initial {
  font-size: 40px;
}

.size-xlarge {
  width: 128px;
  height: 128px;
}

.size-xlarge .ship-initial {
  font-size: 56px;
}
</style>

