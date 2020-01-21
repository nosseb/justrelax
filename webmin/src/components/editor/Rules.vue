<template>
  <div class="d-flex flex-row h-100">
    <div class="rules-list">
      <div class="d-flex flex-row mb-3">
        <h2 class="big-noodle size-15 align-self-center mb-0 mr-3">Rules</h2>
        <b-button-group>
          <ButtonSmall class="position-relative" @click="addRule()">
            <i class="far fa-file fa-fw"></i>
            <i class="fas fa-plus bottom-right"></i>
          </ButtonSmall>
          <ButtonSmall class="position-relative">
            <i class="far fa-folder-open fa-fw"></i>
            <i class="fas fa-plus bottom-right"></i>
          </ButtonSmall>
        </b-button-group>
      </div>
      <div class="d-flex flex-column">
        <div v-for="(r, index) in rules" :key="index" class="pointer" @click="displayRule(index)">
          <i class="far fa-file fa-fw"></i> {{ r.name }}
        </div>
      </div>
    </div>
    <div class="container-fluid">
      <div class="row">
        <div v-if="displayedRule === null" class="col">
          Loading...
        </div>
        <div v-else class="col">
          <div class="d-flex flex-row mb-3">
            <div class="mr-3 align-self-center">{{ displayedRule.name }}</div>

            <b-button-group>
              <ButtonSmall class="position-relative" @click="addComponent('trigger')">
                <i class="fas fa-exclamation fa-fw"></i>
                <i class="fas fa-plus bottom-right"></i>
              </ButtonSmall>
              <ButtonSmall class="position-relative" @click="addComponent('condition')">
                <i class="fas fa-question fa-fw"></i>
                <i class="fas fa-plus bottom-right"></i>
              </ButtonSmall>
              <ButtonSmall class="position-relative" @click="addComponent('action')">
                <i class="fas fa-play fa-fw"></i>
                <i class="fas fa-plus bottom-right"></i>
              </ButtonSmall>
            </b-button-group>
          </div>

          <div class="container-fluid">
            <div class="row mb-2">
              <div class="col">
                <Context
                  :title="'Triggers'"
                  :type="'trigger'"
                  :components="displayedRule.triggers"
                  @updateComponent="(index, c) => updateComponent('trigger', index, c)"
                />
              </div>
            </div>
            <div class="row mb-2">
              <div class="col">
                <Context
                  :title="'Conditions'"
                  :type="'condition'"
                  :components="displayedRule.conditions"
                  @updateComponent="(index, c) => updateComponent('condition', index, c)"
                />
              </div>
            </div>
            <div class="row">
              <div class="col">
                <Context
                  :title="'Actions'"
                  :type="'action'"
                  :components="displayedRule.actions"
                  @updateComponent="(index, c) => updateComponent('action', index, c)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ButtonSmall from "@/components/common/ButtonSmall"
import Context from "@/components/editor/Context.vue"
import editorStore from "@/store/editorStore.js"

export default {
  name: 'TabRules',
  components: {
    ButtonSmall,
    Context,
  },
  data() {
    return {
      displayedRuleIndex: 0,
    }
  },
  computed: {
    rules: function() {
      return editorStore.state.rules
    },
    displayedRule: function() {
      if (editorStore.state.rules[this.displayedRuleIndex] === undefined) {
        return null
      } else {
        return editorStore.state.rules[this.displayedRuleIndex]
      }
    },
  },
  methods: {
    displayRule: function(index) {
      this.displayedRuleIndex = index
    },
    addRule: function() {
      editorStore.commit('addRule')
    },
    addComponent: function(context) {
      let ruleIndex = this.displayedRuleIndex
      editorStore.commit('addComponent', {ruleIndex, context})
    },
    updateComponent: function(context, componentIndex, component) {
      let ruleIndex = this.displayedRuleIndex
      editorStore.commit('updateComponent', {ruleIndex, context, componentIndex, component})
    },
  }
}
</script>

<style scoped>
.rules-list {
  border-right: rgba(248, 249, 250, 0.2) 1px solid;
  padding-right: 15px;
  width: 200px;
}

.bottom-right {
  position: absolute;
  bottom: 0.2rem;
  right: 0.2rem;
  font-size: 70%;
}
</style>