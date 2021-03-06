import gpiozero

from twisted.internet import reactor

from justrelax.node.service import JustSockClientService, EventCategoryToMethodMixin


class Rotary:
    POSITIONS = 20

    def __init__(self, clk_pin, dt_pin, callback):
        self.clk = gpiozero.InputDevice(clk_pin, pull_up=False)
        self.dt = gpiozero.InputDevice(dt_pin, pull_up=False)
        self.callback = callback

        self.position = 5

        self.task = None

    def enable(self):
        self.check_delta(self.clk.value)

    def disable(self):
        if self.task and self.task.active():
            self.task.cancel()

    def check_delta(self, last_clk_value):
        clk_value = self.clk.value
        dt_value = self.dt.value

        if clk_value != last_clk_value:
            if dt_value != clk_value:
                new_position = (self.position + 1) % self.POSITIONS
            else:
                new_position = (self.position - 1) % self.POSITIONS

            if self.position != new_position:
                self.position = new_position
                self.callback(self.position)

        self.task = reactor.callLater(0, self.check_delta, clk_value)


class DecorationBeltRotary(EventCategoryToMethodMixin, JustSockClientService):
    class PROTOCOL:
        CATEGORY = "category"

        NEW_POSITION = "new_position"
        POSITION = "position"

    def __init__(self, *args, **kwargs):
        super(DecorationBeltRotary, self).__init__(*args, **kwargs)

        clk_pin = self.node_params["clk_pin"]
        dt_pin = self.node_params["dt_pin"]

        self.rotary = Rotary(clk_pin, dt_pin, self.notify_new_position)

    def notify_new_position(self, position):
        self.send_event(
            {
                self.PROTOCOL.CATEGORY: self.PROTOCOL.NEW_POSITION,
                self.PROTOCOL.POSITION: position
            }
        )

    def event_enable(self):
        self.rotary.enable()

    def event_disable(self):
        self.rotary.disable()
