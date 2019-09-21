import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex);

var store = new Vuex.Store({
  state: {
    tableHeight: 900,
    tableWidth: 900,
    mouseX: 0,
    lastMouseX: null,
    mouseY: 0,
    lastMouseY: null,
    blocks: [
      {
        color: "#c53500",
        left: 0,
        top: 0,
        width: 150,
        height: 300,
        dragging: false,
        verticalDrag: true,
        horizontalDrag: false,
        zIndex: 10,
      },
      {
        color: "#c53500",
        left: 300,
        top: 0,
        width: 300,
        height: 150,
        dragging: false,
        verticalDrag: false,
        horizontalDrag: true,
        zIndex: 10,
      },
      {
        color: "#c53500",
        left: 0,
        top: 300,
        width: 300,
        height: 150,
        dragging: false,
        verticalDrag: false,
        horizontalDrag: true,
        zIndex: 10,
      },
      {
        color: "#c53500",
        left: 450,
        top: 450,
        width: 150,
        height: 150,
        dragging: false,
        verticalDrag: true,
        horizontalDrag: true,
        zIndex: 10,
      },
    ],
    dragging: null,
    zIndexCounter: 10,
    articles: [
      [{name: "apple"}, {name: "orange"}, {name: "raisins"}, {name: "leek"}, {name: "raisins"}, {name: "leek"}],
      [{name: "pear"}, {name: "lemon"}, {name: "strawberry"}, {name: "fish"}, {name: "raisins"}, {name: "leek"}],
      [{name: "protob"}, {name: "rice"}, {name: "water"}, {name: "grains"}, {name: "raisins"}, {name: "leek"}],
      [{name: "powder"}, {name: "pill"}, {name: "milk"}, {name: "coffee"}, {name: "raisins"}, {name: "leek"}],
      [{name: "protob"}, {name: "rice"}, {name: "water"}, {name: "grains"}, {name: "raisins"}, {name: "leek"}],
      [{name: "powder"}, {name: "pill"}, {name: "milk"}, {name: "coffee"}, {name: "raisins"}, {name: "leek"}],
    ],
    logs: [],
    carriageReturns: 0,
    typingLogs: false,
  },
  mutations: {
    appMousemove (state, event) {
      if (state.lastMouseX === null) {
        state.lastMouseX = event.clientX
      } else {
        state.lastMouseX = state.mouseX
      }

      if (state.lastMouseY === null) {
        state.lastMouseY = event.clientY
      } else {
        state.lastMouseY = state.mouseY
      }

      state.mouseX = event.clientX
      state.mouseY = event.clientY

      var deltaX = state.mouseX - state.lastMouseX
      var deltaY = state.mouseY - state.lastMouseY
      if (state.dragging !== null) {

        var i = 0
        if (state.blocks[state.dragging].horizontalDrag === true) {
          if (deltaX > 0) {
            // going right
            var firstObstacleLeft = state.tableHeight
            var draggedBlockRight = state.blocks[state.dragging].left + state.blocks[state.dragging].width

            for (i = 0 ; i < state.blocks.length ; i++) {
              if (state.dragging == i) {
                continue
              }

              if ((state.blocks[state.dragging].top >= state.blocks[i].top + state.blocks[i].height) ||
                  (state.blocks[state.dragging].top + state.blocks[state.dragging].height <= state.blocks[i].top)) {
                continue
              }

              if (draggedBlockRight > state.blocks[i].left) {
                continue
              }

              firstObstacleLeft = Math.min(firstObstacleLeft, state.blocks[i].left)
            }

            state.blocks[state.dragging].left = Math.min(state.blocks[state.dragging].left + deltaX, firstObstacleLeft - state.blocks[state.dragging].width)
          } else if (deltaX < 0) {
            // going left
            var firstObstacleRight = 0 // 0 is the left border
            var futureDraggedBlockLeft = state.blocks[state.dragging].left + deltaX

            for (i = 0 ; i < state.blocks.length ; i++) {
              if (state.dragging == i) {
                continue
              }

              var iBlockRight = state.blocks[i].left + state.blocks[i].width

              if ((state.blocks[state.dragging].top >= state.blocks[i].top + state.blocks[i].height) ||
                  (state.blocks[state.dragging].top + state.blocks[state.dragging].height <= state.blocks[i].top)) {
                continue
              }

              if (state.blocks[state.dragging].left < iBlockRight) {
                continue
              }

              firstObstacleRight = Math.max(firstObstacleRight, iBlockRight)
            }

            state.blocks[state.dragging].left = Math.max(futureDraggedBlockLeft, firstObstacleRight)
          }
        }

        if (state.blocks[state.dragging].verticalDrag === true) {
          if (deltaY > 0) {
            // going bottom
            var firstObstacleTop = state.tableHeight
            var draggedBlockBottom = state.blocks[state.dragging].top + state.blocks[state.dragging].height

            for (i = 0 ; i < state.blocks.length ; i++) {
              if (state.dragging == i) {
                continue
              }

              if ((state.blocks[state.dragging].left >= state.blocks[i].left + state.blocks[i].width) ||
                  (state.blocks[state.dragging].left + state.blocks[state.dragging].width <= state.blocks[i].left)) {
                continue
              }

              if (draggedBlockBottom > state.blocks[i].top) {
                continue
              }

              firstObstacleTop = Math.min(firstObstacleTop, state.blocks[i].top)
            }

            state.blocks[state.dragging].top = Math.min(state.blocks[state.dragging].top + deltaY, firstObstacleTop - state.blocks[state.dragging].height)
          } else if (deltaY < 0) {
            // going top
            var firstObstacleBottom = 0 // 0 is the top border
            var futureDraggedBlockTop = state.blocks[state.dragging].top + deltaY

            for (i = 0 ; i < state.blocks.length ; i++) {
              if (state.dragging == i) {
                continue
              }

              var iBlockBottom = state.blocks[i].top + state.blocks[i].height

              if ((state.blocks[state.dragging].left >= state.blocks[i].left + state.blocks[i].width) ||
                  (state.blocks[state.dragging].left + state.blocks[state.dragging].width <= state.blocks[i].left)) {
                continue
              }

              if (state.blocks[state.dragging].top < iBlockBottom) {
                continue
              }

              firstObstacleBottom = Math.max(firstObstacleBottom, iBlockBottom)
            }

            state.blocks[state.dragging].top = Math.max(futureDraggedBlockTop, firstObstacleBottom)
          }
        }
      }
    },
    // eslint-disable-next-line
    processEvent (state, event) {
      if (event.type == 'log') {
        state.logs.push({
          level: event.level,
          message: event.message,
          displayedMessage: '',
          displayedChars: -1,
        })
        state.carriageReturns += 1
        updateDisplayedMessages()
      }
    },
    blockMousedown (state, id) {
      state.dragging = id
      state.zIndexCounter += 1
      state.blocks[id].zIndex = state.zIndexCounter
    },
    appMouseup (state) {
      state.dragging = null
    },
    appMouseleave (state) {
      state.dragging = null
    },
    lockTypingLogs(state) {
      state.typingLogs = true
    },
    unlockTypingLogs(state) {
      state.typingLogs = false
    },
    typeOneChar(state, logIndex) {
      state.logs[logIndex].displayedChars += 1
      state.logs[logIndex].displayedMessage += state.logs[logIndex].message[state.logs[logIndex].displayedChars]
    },
    typeCarriageReturn(state, logIndex) {
      state.carriageReturns += 1
      state.logs[logIndex].displayedMessage += '<br>'
    }
  },
})

function updateDisplayedMessages() {
  if (store.state.typingLogs === true) {
    return
  }
  store.commit('lockTypingLogs')

  _updateDisplayedMessages()
}

function _updateDisplayedMessages() {
  for (var i = 0 ; i < store.state.logs.length ; i++) {
    if (store.state.logs[i].displayedChars < store.state.logs[i].message.length - 1) {
      store.commit('typeOneChar', i)
      if (store.state.logs[i].level == 'info') {
        if (store.state.logs[i].displayedChars % 29 - 24 == 0) {
          store.commit('typeCarriageReturn', i)
        }
      } else if (store.state.logs[i].level == 'warning') {
        if (store.state.logs[i].displayedChars % 29 - 21 == 0) {
          store.commit('typeCarriageReturn', i)
        }
      }
      setTimeout(_updateDisplayedMessages, 75)
      return
    }
  }

  store.commit('unlockTypingLogs')
}

export default store
