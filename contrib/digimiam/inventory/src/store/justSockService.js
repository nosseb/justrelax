import Vue from 'vue'
import Vuex from 'vuex'

import i18n from '@/locales.js'
import router from '@/router.js'
import sokobanStore from '@/store/sokobanStore.js'
import logStore from '@/store/logStore.js'
import progressionStore from '@/store/progressionStore.js'

Vue.use(Vuex)

const justSockService = new Vuex.Store({
  mutations: {
    SOCKET_ONOPEN (state, event) {
      Vue.prototype.$socket = event.currentTarget
      let iamMessage = {
        message_type: "IAM",
        client_type: "node",
        channel: "digimiam1",
        name: "inventory",
      }
      Vue.prototype.$socket.send(JSON.stringify(iamMessage))
    },
    SOCKET_ONCLOSE (state, event) {
      // eslint-disable-next-line
      console.error(state, event)
    },
    SOCKET_ONERROR (state, event) {
      // eslint-disable-next-line
      console.error(state, event)
    },
    SOCKET_ONMESSAGE (state, rawMessage) {
      let message = JSON.parse(rawMessage.data)
      if (message.message_type != 'EVENT') {
        return
      }

      let event = message.event
      if (event.category == 'reset') {
        // Reload page
        router.go()
      } else if (event.category == 'l10n') {
        let query = JSON.parse(JSON.stringify(router.app.$route.query))
        if (event.lang == 'fr') {
          if (i18n.locale != 'fr') {
            query.lang = 'fr'
            router.push({path: '/', query: query})
          }
          i18n.locale = 'fr'
        } else {
          if (i18n.locale != 'en') {
            query.lang = 'en'
            router.push({path: '/', query: query})
          }
          i18n.locale = 'en'
        }
      } else if (event.category == 'log') {
        let logMessage = event.message
        let level = event.level
        let useLocale = event.use_locale
        logStore.commit('processLog', {logMessage, level, useLocale})
      } else if (event.category === 'lock_difficulty') {
        sokobanStore.commit('lockDifficulty')
      } else if (event.category === 'set_difficulty') {
        sokobanStore.commit('setDifficulty', event.difficulty)
      } else if (event.category === 'move') {
        sokobanStore.commit('move', event.direction)
      } else if (event.category === 'display_danger_window') {
        progressionStore.commit('displayDangerWindow')
      }
    },
    SOCKET_RECONNECT (state, count) {
      // eslint-disable-next-line
      console.info(state, count)
    },
    // eslint-disable-next-line
    SOCKET_RECONNECT_ERROR (state) {
      // eslint-disable-next-line
      console.error("Reconnect error")
    },
    sendEvent (state, event) {
      let message = {
        message_type: "EVENT",
        event: event,
      }
      let jsonMessage = JSON.stringify(message)
      Vue.prototype.$socket.send(jsonMessage)
    },
  },
})

export default justSockService
