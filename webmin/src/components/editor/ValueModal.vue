<template>
  <b-modal
    :id="modalId"
    body-bg-variant="dark"
    body-text-variant="light"
    @ok="ok"
    @hidden="$emit('hidden')"
  >
    <ValueModalPredefined
      v-if="displayPredefinedSelector"
      :templateName="templateName"
      :predefinedChoices="predefinedChoices"
      :parentValue="value"
      :checked="selectedSource === 'predefined'"
      @pushValue="(newValue) => updateValueBuffer('predefined', newValue)"
    />

    <ValueModalVariable
      v-if="displayVariableSelector"
      :parentValue="value"
      :inputType="inputType"
      :checked="selectedSource === 'variable'"
      @pushValue="(newValue) => updateValueBuffer('variable', newValue)"
    />

    <ValueModalFunction
      v-if="displayFunctionSelector"
      :modalId="modalId"
      :parentValue="value"
      :inputType="inputType"
      :checked="selectedSource === 'function'"
      @pushValue="(newValue) => updateValueBuffer('function', newValue)"
    />

    <ValueModalString
      v-if="displayStringSelector"
      :parentValue="value"
      :checked="selectedSource === 'string'"
      @pushValue="(newValue) => updateValueBuffer('string', newValue)"
    />

    <ValueModalInteger
      v-if="displayIntegerSelector"
      :parentValue="value"
      :checked="selectedSource === 'integer'"
      @pushValue="(newValue) => updateValueBuffer('integer', newValue)"
    />

    <ValueModalReal
      v-if="displayRealSelector"
      :parentValue="value"
      :checked="selectedSource === 'real'"
      @pushValue="(newValue) => updateValueBuffer('real', newValue)"
    />

    <ValueModalBoolean
      v-if="displayBooleanSelector"
      :parentValue="value"
      :checked="selectedSource === 'boolean'"
      @pushValue="(newValue) => updateValueBuffer('boolean', newValue)"
    />
  </b-modal>
</template>

<script>
import ValueModalPredefined from '@/components/editor/ValueModalPredefined.vue'
import ValueModalVariable from '@/components/editor/ValueModalVariable.vue'
import ValueModalFunction from '@/components/editor/ValueModalFunction.vue'
import ValueModalString from '@/components/editor/ValueModalString.vue'
import ValueModalInteger from '@/components/editor/ValueModalInteger.vue'
import ValueModalReal from '@/components/editor/ValueModalReal.vue'
import ValueModalBoolean from '@/components/editor/ValueModalBoolean.vue'

export default {
  name: "ValueModal",
  components: {
    ValueModalPredefined,
    ValueModalVariable,
    ValueModalFunction,
    ValueModalString,
    ValueModalInteger,
    ValueModalReal,
    ValueModalBoolean,
  },
  data() {
    return {
      valueBuffer: undefined,
      selectedSource: "string",
    }
  },
  computed: {
    displayPredefinedSelector() {
       return this.inputType === 'predefined'
    },
    displayVariableSelector() {
      return this.inputType !== 'predefined' || this.inputType === 'variable'
    },
    displayFunctionSelector() {
      return this.inputType !== 'predefined' && this.inputType !== 'variable'
    },
    displayStringSelector() {
      return this.inputType === 'string'
    },
    displayIntegerSelector() {
      return this.inputType === 'integer'
    },
    displayRealSelector() {
      return this.inputType === 'real'
    },
    displayBooleanSelector() {
      return this.inputType === 'boolean'
    },
  },
  methods: {
    ok: function() {
      this.$emit('update', this.valueBuffer)
    },
    updateValueBuffer(source, value) {
      this.selectedSource = source
      this.valueBuffer = value
    },
  },
  props: {
    modalId: String,
    value: [Object, Boolean, String, Number],
    inputType: String,
    templateName: String,
    predefinedChoices: Array,
  },
}
</script>
