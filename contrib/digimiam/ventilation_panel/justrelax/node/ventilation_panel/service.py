import time
import gpiozero
import neopixel
import board

from twisted.internet.reactor import callLater

from justrelax.common.logging_utils import logger
from justrelax.node.service import JustSockClientService, EventCategoryToMethodMixin


class AirSource:
    def __init__(self, name, jack_port_pin):
        self.name = name
        self.jack_port = gpiozero.InputDevice(jack_port_pin)

    def is_active(self):
        return self.jack_port.is_active

    def __str__(self):
        return self.name


class AirDuct:
    def __init__(self, name, air_duct_controller, fan_pin, jack_pin, led_index):
        self.name = name
        self.ad_controller = air_duct_controller
        self.fan = gpiozero.OutputDevice(fan_pin)
        self.jack = gpiozero.OutputDevice(jack_pin)
        self.led_index = led_index
        self.connected_source = None
        self.last_connected_sources = []

    def set_color(self, color):
        r, g, b = self.ad_controller.get_color_rgb(color)
        self.ad_controller.led_strip[self.led_index] = (r, g, b)

    def check_connection(self):
        connection_found = False
        self.jack.on()
        for as_ in self.ad_controller.air_sources.values():
            if as_.is_active():
                if self.connected_source is not as_:
                    self.connected_source = as_
                    self.ad_controller.on_connect(self, as_)
                connection_found = True
                break

        if not connection_found:
            if self.connected_source is not None:
                self.connected_source = None
                self.ad_controller.on_disconnect(self)
        self.jack.off()

    def __str__(self):
        return self.name


class VentilationController:
    STATUSES = {"inactive", "playing", "success"}

    def __init__(self, ventilation_panel_service, initial_difficulty, difficulties, air_ducts, air_sources, colors):
        self.service = ventilation_panel_service

        self._status = None

        self.difficulties = difficulties
        self._difficulty = list(self.difficulties)[0]  # By default. Not reliable
        self.difficulty = initial_difficulty

        self.led_strip = neopixel.NeoPixel(board.D18, 6)

        self.try_counters = {}  # keys are round indexes, values are counters
        self.sequence_cursor = -1  # -1 <=> game is not running
        self.success_sequence = []
        self.round = 0

        self.air_sources = {}
        for as_name, as_ in air_sources.items():
            self.air_sources[as_name] = AirSource(as_name, as_["jack_port_pin"])

        self.air_ducts = {}
        for ad_name, ad in air_ducts.items():
            self.air_ducts[ad_name] = AirDuct(
                ad_name, self, ad["fan_pin"], ad["jack_pin"], ad["led_index"])

        self.colors = colors

        self.check_jacks_task = callLater(1, self.check_jacks)
        self.animation_tasks = {}
        self.unskippable_animation_task = None

    @property
    def difficulty(self):
        return self._difficulty

    @difficulty.setter
    def difficulty(self, value):
        if value not in self.difficulties:
            logger.warning("Difficulty {} not in {}: skipping".format(value, ", ".join(self.difficulties)))
        else:
            logger.debug("Setting difficulty to {}".format(value))
            self._difficulty = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if value not in self.STATUSES:
            logger.warning("Status {} not in {}: skipping".format(value, ", ".join(self.STATUSES)))
            return

        if value == self.status:
            logger.debug("Status is already {}: skipping".format(value))
            return

        logger.debug("Setting status to {}".format(value))
        self._status = value

        if self._status == "inactive":
            self.skip_skippable_animations()

            if self.unskippable_animation_task and self.unskippable_animation_task.active():
                self.unskippable_animation_task.cancel()
            self.on_inactive()

        elif self._status == "playing":
            self.skip_skippable_animations()

            if self.unskippable_animation_task and self.unskippable_animation_task.active():
                self.unskippable_animation_task.cancel()
            self.on_playing()

        elif self._status == "success":
            self.on_success()

    def skip_skippable_animations(self):
        for ad in self.air_ducts.values():
            self.led_strip[ad.led_index] = (0, 0, 0)
        for task in self.animation_tasks.values():
            if task.active():
                task.cancel()

    def get_color_rgb(self, color):
        predefined_color = self.colors.get(color, {})
        r = predefined_color.get("r", 0)
        g = predefined_color.get("g", 0)
        b = predefined_color.get("b", 0)
        return r, g, b

    def on_inactive(self):
        for ad in self.air_ducts.values():
            ad.fan.off()
        self.led_strip.fill((0, 0, 0))

    def on_playing(self):
        self.led_strip.fill((0, 0, 0))
        self.sequence_cursor = -1
        self.round = 0
        self.try_counters = {}
        # Force players to take an action before the game restarts
        self.display_connected_air_ducts_before_restart()

    def on_success(self):
        self.service.notify_success()

    def on_connect(self, air_duct, air_source):
        logger.debug("{} is connected to {}".format(air_duct, air_source))

        if self.status != "playing":
            logger.debug("Game is not started yet: nothing to do")
            return

        if self.sequence_cursor != -1:  # Game is running
            if self.success_sequence[self.sequence_cursor]["air_duct"] != air_duct.name:
                logger.debug("Expecting {} to be connected".format(
                    self.success_sequence[self.sequence_cursor]["air_duct"]))
                self.sequence_cursor = -1
                self.bad_move_failure_animation()

            else:
                try:
                    expected_air_sources = self.get_expected_sources(self.sequence_cursor)
                except Exception:
                    expected_air_sources = set()
                    good_connection = True
                else:
                    good_connection = air_source in expected_air_sources

                if not good_connection:
                    logger.debug("Expecting connection with {}".format(
                        " or ".join([str(s) for s in expected_air_sources])))
                    self.sequence_cursor = -1
                    self.bad_move_failure_animation()

                else:
                    logger.debug("Good connection")
                    air_duct.fan.on()
                    air_duct.last_connected_sources.append(air_source)  # Keep track of the good history
                    if self.sequence_cursor == len(self.success_sequence) - 1:
                        self.sequence_cursor = -1
                        self.on_round_complete()
                    else:
                        self.sequence_cursor += 1
                        logger.debug("Expecting element {} (cursor is {})".format(
                            self.success_sequence[self.sequence_cursor], self.sequence_cursor))
                        self.good_move_animation()

        else:  # Game is not running
            logger.debug("Game is not running: updating errors")
            self.display_connected_air_ducts_before_restart()

    def on_disconnect(self, air_duct):
        logger.debug("{} is not connected to any air source".format(air_duct))

        if self.status != "playing":
            logger.debug("Game is not started yet: nothing to do")
            return

        if self.sequence_cursor != -1:  # Game is running
            air_duct.fan.off()
            if self.success_sequence[self.sequence_cursor]["air_duct"] != air_duct.name:
                # It was not necessary to disconnect this air duct: considering as an error
                # TODO: reactivate this rule
                logger.debug("Should be considered an error but ignoring for now")
                # self.sequence_cursor = -1
                # self.bad_move_failure_animation()
        else:  # Game is not running
            if all([ad.connected_source is None for ad in self.air_ducts.values()]):
                logger.debug("All air ducts are disconnected")
                self.restart_round()
            else:
                logger.debug("Some air ducts remain connected")
                self.display_connected_air_ducts_before_restart()

    def on_round_complete(self):
        logger.debug("Round {} complete".format(self.round))

        def step1():
            self.good_move_animation()
            self.unskippable_animation_task = callLater(1.3, step2)

        def step2():
            self.good_move_animation_reversed()
            self.unskippable_animation_task = callLater(1.3, step3)

        def step3():
            self.blink(self.round, "light_green", 5)
            for ad in self.air_ducts.values():
                ad.fan.off()
            self.unskippable_animation_task = callLater(1.3, step4)

        def step4():
            if self.round < 2:
                logger.debug("Going to next round".format(self.round))
                self.round += 1
                if all([ad.connected_source is None for ad in self.air_ducts.values()]):
                    self.restart_round()
                else:
                    self.display_connected_air_ducts_before_restart()
            else:
                logger.debug("All rounds have been completed: victory!")
                self.success_animation(step5)

        def step5():
            self.status = "success"

        step1()

    def new_success_sequence(self):
        logger.debug("Loading a new success sequence (try counter={})".format(self.try_counters[self.round]))

        round_sequences = self.difficulties[self.difficulty][self.round]
        sequence_index = (self.try_counters[self.round] - 1) % len(round_sequences)

        self.success_sequence = round_sequences[sequence_index]

        logger.info("The new success sequence is {}".format(self.success_sequence))

    def display_sequence(self):
        logger.info("Displaying sequence")

        self.skip_skippable_animations()

        def pre_display_animation():
            self.unskippable_animation_task = callLater(1.6, display_element)
            for ad in self.air_ducts.values():
                ad.set_color("black")
                self.fluid_to_color(
                    ad.led_index,
                    "red",
                    0.1,
                    "display_element",
                    self.fluid_to_color,
                    ad.led_index,
                    "black",
                    0.1,
                    "display_element",
                    self.fluid_to_color,
                    ad.led_index,
                    "red",
                    0.1,
                    "display_element",
                    self.fluid_to_color,
                    ad.led_index,
                    "black",
                    0.1,
                    "display_element",
                    self.fluid_to_color,
                    ad.led_index,
                    "red",
                    0.1,
                    "display_element",
                    self.fluid_to_color,
                    ad.led_index,
                    "black",
                    0.1,
                    "display_element",
                )

        def display_element(index=0):
            if index < len(self.success_sequence):
                # For the last element of the sequence, this code saves a task in the unskippable_animation_task,
                # ensuring that the animation time lasts until the last led has turned black again.
                self.unskippable_animation_task = callLater(2, display_element, index + 1)
                element = self.success_sequence[index]

                self.air_ducts[element["air_duct"]].fan.on()
                self.animation_tasks["fan"] = callLater(1.4, self.air_ducts[element["air_duct"]].fan.off)

                self.fluid_to_color(
                    self.air_ducts[element["air_duct"]].led_index,
                    element["color"],
                    1,
                    "display_element",
                    self.fluid_to_color,
                    self.air_ducts[element["air_duct"]].led_index,
                    "black",
                    1,
                    "display_element",
                )

        pre_display_animation()

    def get_expected_sources(self, cursor):
        displayed_color = self.success_sequence[cursor]["color"]

        if displayed_color == "pink":
            return self.get_expected_sources(cursor - 1)

        elif displayed_color == "purple":
            return self.get_expected_sources(cursor + 1)

        elif displayed_color == "white":
            return {self.air_sources["as0"]}

        elif displayed_color == "yellow":
            return {self.air_sources["as1"]}

        elif displayed_color == "orange":
            duct = self.air_ducts[self.success_sequence[cursor]["air_duct"]]
            lcs = duct.last_connected_sources
            if self.air_sources["as0"] in lcs or self.air_sources["as1"] in lcs:
                return {self.air_sources["as2"]}
            else:
                return {self.air_sources["as1"]}

        elif displayed_color == "blue":
            duct = self.air_ducts[self.success_sequence[cursor]["air_duct"]]

            if len(duct.last_connected_sources) < 1:
                raise ValueError(
                    "Blue cannot be the first color given to an air duct (in the sequence {})".format(
                        self.success_sequence))

            last_source = duct.last_connected_sources[-1]

            if last_source.name == "as2":
                return {self.air_sources["as0"], self.air_sources["as1"]}
            elif last_source.name == "as1":
                return {self.air_sources["as0"]}
            else:
                raise ValueError(
                    "Blue cannot be given to an air duct after it is connected to as0 (in the sequence {})".format(
                        self.success_sequence))

        else:
            # Should never happen
            raise NotImplementedError(
                "Color {} is not known to the sequence checker: aborting".format(displayed_color))

    def blink(self, led_index, color, times, cb=None, *cb_args, **cb_kwargs):
        def blink_loop(iteration=times, toggle=True):
            self.led_strip[led_index] = self.get_color_rgb(color if toggle else "black")

            iteration -= 1
            if iteration > 0:
                self.unskippable_animation_task = callLater(
                    0.1, blink_loop, iteration, not toggle)
            else:
                if cb:
                    cb(*cb_args, **cb_kwargs)
        blink_loop()

    def fluid_to_color(self, led_index, color, duration, task_id="fluid_to_color", cb=None, *cb_args, **cb_kwargs):
        t_initial = time.monotonic()
        target_r, target_g, target_b = self.get_color_rgb(color)
        initial_r, initial_g, initial_b = self.led_strip[led_index]

        def animation(t_start, t_last_call):
            now = time.monotonic()
            percentage = (t_last_call - t_start) / duration

            if percentage > 1:
                self.led_strip[led_index] = (
                    target_r,
                    target_g,
                    target_b,
                )
                if cb:
                    cb(*cb_args, **cb_kwargs)
            else:
                self.animation_tasks[task_id] = callLater(
                    0, animation, t_start, now)

                if initial_r > target_r:
                    new_r = int(initial_r - (initial_r - target_r) * percentage)
                else:
                    new_r = int(initial_r + (target_r - initial_r) * percentage)
                if initial_g > target_g:
                    new_g = int(initial_g - (initial_g - target_g) * percentage)
                else:
                    new_g = int(initial_g + (target_g - initial_g) * percentage)
                if initial_b > target_b:
                    new_b = int(initial_b - (initial_b - target_b) * percentage)
                else:
                    new_b = int(initial_b + (target_b - initial_b) * percentage)

                self.led_strip[led_index] = (
                    new_r,
                    new_g,
                    new_b,
                )

        animation(t_initial, t_initial)

    def success_animation(self, callback):
        logger.debug("Running success animation")

        def step1():
            self.led_strip[0] = self.get_color_rgb("black")
            self.led_strip[1] = self.get_color_rgb("black")
            self.led_strip[2] = self.get_color_rgb("black")
            self.unskippable_animation_task = callLater(0.1, step2)

        def step2():
            self.led_strip[0] = self.get_color_rgb("light_green")
            self.unskippable_animation_task = callLater(0.1, step3)

        def step3():
            self.led_strip[1] = self.get_color_rgb("light_green")
            self.unskippable_animation_task = callLater(0.1, step4)

        def step4():
            self.led_strip[2] = self.get_color_rgb("light_green")
            self.unskippable_animation_task = callLater(0.1, step5)

        def step5():
            self.led_strip[3] = self.get_color_rgb("light_green")
            self.unskippable_animation_task = callLater(0.1, step6)

        def step6():
            self.led_strip[0] = self.get_color_rgb("black")
            self.unskippable_animation_task = callLater(0.1, step7)

        def step7():
            self.led_strip[1] = self.get_color_rgb("black")
            self.unskippable_animation_task = callLater(0.1, step8)

        def step8():
            self.led_strip[2] = self.get_color_rgb("black")
            self.unskippable_animation_task = callLater(0.1, step9)

        def step9():
            self.led_strip[0] = self.get_color_rgb("light_green")
            self.led_strip[1] = self.get_color_rgb("light_green")
            self.led_strip[2] = self.get_color_rgb("light_green")
            self.unskippable_animation_task = callLater(1, callback)

        step1()

    def good_move_animation(self):
        logger.debug("Running good move animation")

        self.skip_skippable_animations()

        self.animation_tasks["blink1"] = callLater(
            0,
            self.fluid_to_color, self.air_ducts["ad0"].led_index, "green", 0.35, "blink1",
            self.fluid_to_color, self.air_ducts["ad0"].led_index, "black", 0.35, "blink1",
        )
        self.animation_tasks["blink2"] = callLater(
            0.3,
            self.fluid_to_color, self.air_ducts["ad1"].led_index, "green", 0.35, "blink2",
            self.fluid_to_color, self.air_ducts["ad1"].led_index, "black", 0.35, "blink2",
        )
        self.animation_tasks["blink2"] = callLater(
            0.6,
            self.fluid_to_color, self.air_ducts["ad2"].led_index, "green", 0.35, "blink3",
            self.fluid_to_color, self.air_ducts["ad2"].led_index, "black", 0.35, "blink3",
        )

    def good_move_animation_reversed(self):
        logger.debug("Running reversed good move animation")

        self.skip_skippable_animations()

        self.animation_tasks["blink1"] = callLater(
            0,
            self.fluid_to_color, self.air_ducts["ad2"].led_index, "green", 0.35, "blink1",
            self.fluid_to_color, self.air_ducts["ad2"].led_index, "black", 0.35, "blink1",
        )
        self.animation_tasks["blink2"] = callLater(
            0.3,
            self.fluid_to_color, self.air_ducts["ad1"].led_index, "green", 0.35, "blink2",
            self.fluid_to_color, self.air_ducts["ad1"].led_index, "black", 0.35, "blink2",
        )
        self.animation_tasks["blink2"] = callLater(
            0.6,
            self.fluid_to_color, self.air_ducts["ad0"].led_index, "green", 0.35, "blink3",
            self.fluid_to_color, self.air_ducts["ad0"].led_index, "black", 0.35, "blink3",
        )

    def bad_move_failure_animation(self):
        logger.debug("Running bad move failure animation")

        self.skip_skippable_animations()

        for ad in self.air_ducts.values():
            ad.fan.off()

        def wait_and_display_connected_air_ducts_before_restart():
            self.animation_tasks["wait"] = callLater(
                0.3, self.display_connected_air_ducts_before_restart)

        self.animation_tasks["blink1"] = callLater(
            0,
            self.fluid_to_color, self.air_ducts["ad2"].led_index, "red", 0.35, "blink1",
            self.fluid_to_color, self.air_ducts["ad2"].led_index, "black", 0.35, "blink1",
        )
        self.animation_tasks["blink2"] = callLater(
            0.3,
            self.fluid_to_color, self.air_ducts["ad1"].led_index, "red", 0.35, "blink2",
            self.fluid_to_color, self.air_ducts["ad1"].led_index, "black", 0.35, "blink2",
        )
        self.animation_tasks["blink3"] = callLater(
            0.6,
            self.fluid_to_color, self.air_ducts["ad0"].led_index, "red", 0.35, "blink3",
            self.fluid_to_color, self.air_ducts["ad0"].led_index, "black", 0.35, "blink3",
            wait_and_display_connected_air_ducts_before_restart,
        )

    def display_connected_air_ducts_before_restart(self):
        logger.debug("Displaying connected air ducts in red before restart")

        for ad_name, ad in self.air_ducts.items():
            if ad.connected_source is None:
                ad.set_color("black")
            else:
                ad.set_color("red")

    def restart_round(self):
        logger.debug("Restarting round")
        for ad in self.air_ducts.values():
            ad.set_color("black")
            ad.last_connected_sources = []

        if self.round in self.try_counters:
            self.try_counters[self.round] += 1
        else:
            self.try_counters[self.round] = 1

        self.new_success_sequence()
        self.sequence_cursor = 0

        self.unskippable_animation_task = callLater(0.5, self.display_sequence)

    def reset(self):
        self.status = "inactive"

    def check_jacks(self):
        self.check_jacks_task = callLater(0.1, self.check_jacks)
        if not (self.unskippable_animation_task and self.unskippable_animation_task.active()):
            for ad in self.air_ducts.values():
                ad.check_connection()


class VentilationPanel(EventCategoryToMethodMixin, JustSockClientService):
    def __init__(self, *args, **kwargs):
        super(VentilationPanel, self).__init__(*args, **kwargs)

        initial_difficulty = self.node_params["initial_difficulty"]
        air_ducts = self.node_params["air_ducts"]
        air_sources = self.node_params["air_sources"]
        colors = self.node_params["colors"]

        difficulties = {}
        for difficulty, rounds in self.node_params["difficulties"].items():
            difficulties[difficulty] = {}
            for round_index in range(3):
                round_ = "round{}".format(round_index)
                sequences = []
                for raw_sequence in rounds[round_]:
                    elements = [e.strip() for e in raw_sequence.split(",")]
                    sequence = []
                    for element in elements:
                        ad, _, color = element.partition('>')
                        ad = ad.strip()
                        color = color.strip()

                        assert ad in air_ducts, "{} is not declared as an air duct: aborting".format(ad)
                        assert color in colors, "{} is not declared as a color: aborting".format(color)

                        sequence.append({"air_duct": ad, "color": color})
                    sequences.append(sequence)

                difficulties[difficulty][round_index] = sequences

        self.vc = VentilationController(self, initial_difficulty, difficulties, air_ducts, air_sources, colors)

    def event_reset(self):
        self.vc.reset()

    def event_set_status(self, status: str):
        self.vc.status = status

    def event_set_difficulty(self, difficulty: str):
        self.vc.difficulty = difficulty

    def notify_success(self):
        self.send_event({"category": "success"})
