<template>
  <div class="position-relative">
    <div class="container-fluid px-0 h-100">
      <div class="row justify-content-center h-100">
        <div class="w-large">
          <DishMatrix/>
        </div>

        <div class="w-small">
          <MenuDisplay/>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import MenuDisplay from '@/components/MenuDisplay.vue'
import DishMatrix from '@/components/DishMatrix.vue'

export default {
  name: 'MenuSelector',
  components: {
    MenuDisplay,
    DishMatrix,
  },
}
</script>

<style scoped>
.w-large {
  width: 820px;
  padding: 0px 15px;
}

.w-small {
  width: 439.5px;
  padding: 0px 15px;
}
</style>