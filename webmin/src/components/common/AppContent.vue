<template>
  <div class="d-flex flex-column flex-grow-1">
    <header class="h-75px bgc-dark position-sticky top-0">
      <div class="container-fluid h-100">
        <div class="d-flex flex-row justify-content-between align-items-center w-100 h-100">
          <slot name="header-left"></slot>
          <slot name="header-right">
            <NotificationButton/>
          </slot>
        </div>
      </div>
    </header>
    <main class="d-flex flex-row h-100">
      <div class="container-fluid padding-bottom-10rem pt-2">
        <slot name="main"></slot>
      </div>
      <NotificationPanel/>
    </main>
  </div>
</template>

<script>
import NotificationButton from '@/components/notification/Button.vue'
import NotificationPanel from '@/components/notification/Panel.vue'

export default {
  name: 'AppContent',
  components: {
    NotificationButton,
    NotificationPanel
  }
}
</script>

<style scoped>
header {
  z-index: 1;
  box-shadow: 0 0.1rem 0.4rem #2e2e2e;
}

main {
  overflow: hidden;
}
</style>
