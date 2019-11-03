import Vue from 'vue'
import Vuex from 'vuex'

import i18n from '@/locales.js'
import router from '@/router.js'

Vue.use(Vuex);

const justSockService = new Vuex.Store({
  mutations: {
    // eslint-disable-next-line
    SOCKET_ONOPEN (state, event) {
      Vue.prototype.$socket = event.currentTarget
      Vue.prototype.$socket.send(
        JSON.stringify(
          {
            "type": "IAM",
            "content": {
              "client_type": "$node",
              "channel": "digimiam1",
              "name": "root_server",
            }
          }
        )
      )
    },
    SOCKET_ONCLOSE (state, event) {
      // eslint-disable-next-line
      console.error(state, event)
    },
    SOCKET_ONERROR (state, event) {
      // eslint-disable-next-line
      console.error(state, event)
    },
    SOCKET_ONMESSAGE (state, message) {
      var msg = JSON.parse(message.data)
      if (msg.type != 'MSG') {
        return
      }

      var content = msg.content
      if (content.type == 'reset') {
        // Reload page
        router.go()
      } else if (content.type == 'l10n') {
        if (content.lang == 'fr') {
          if (i18n.locale != 'fr') {
            router.push({path: '/', query: {'lang': 'fr'}})
          }
          i18n.locale = 'fr'
        } else {
          if (i18n.locale != 'en') {
            router.push({path: '/', query: {'lang': 'en'}})
          }
          i18n.locale = 'en'
        }
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
    // eslint-disable-next-line
    sendToGateway (state, message) {
      Vue.prototype.$socket.send(message)
    },
  },
  actions: {
    sendToGateway (context, message) {
      context.commit('sendToGateway', message)
    }
  }
})

export default justSockService
