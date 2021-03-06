import json

from autobahn.twisted.websocket import WebSocketServerProtocol

from justrelax.common.logging_utils import logger
from justrelax.common.constants import JUST_SOCK_PROTOCOL as P
from justrelax.common.validation import validate_node_name, validate_channel


class JustSockServerProtocol(WebSocketServerProtocol):
    def __init__(self):
        super(JustSockServerProtocol, self).__init__()
        self.name = None
        self.channel = None
        self.client_type = None

    def onConnect(self, request):
        logger.info("Node connecting: {}".format(request.peer))

    def onOpen(self):
        logger.info("Node connected: {}".format(self.peer))

    def connectionLost(self, reason):
        if self.client_type == P.CLIENT_ADMIN:
            identifier = self.name
            self.factory.unregister_admin(self)
        elif self.client_type == P.CLIENT_NODE:
            identifier = "{}@{}".format(self.name, self.channel)
            self.factory.unregister_node(self)
        else:
            identifier = self.peer

        logger.info("Lost connection with {}".format(identifier))

    def onMessage(self, payload, isBinary):
        if isBinary:
            logger.warning("Binary message received ({} bytes): ignoring".format(len(payload)))
            return

        try:
            unicode_message = payload.decode('utf8')
        except UnicodeDecodeError:
            logger.exception("Cannot load {}: ignoring".format(payload))
            return

        try:
            message = json.loads(unicode_message)
        except json.JSONDecodeError:
            logger.exception("Cannot load {}: ignoring".format(unicode_message))
            return

        ok, warning = self.validate_message(message)
        if not ok:
            logger.info("Received {}".format(message))
            logger.warning(warning)
            logger.info("Ignoring")
        else:
            logger.debug("Received {}".format(message))

            self.log_message(message, to_server=True)

            if self.client_type == P.CLIENT_NODE:
                if message[P.MESSAGE_TYPE] == P.MESSAGE_TYPE_EVENT:
                    event = message[P.EVENT]
                    self.factory.process_event(self.name, self.channel, event)
                elif message[P.MESSAGE_TYPE] == P.MESSAGE_TYPE_LOG:
                    level = message[P.LOG_LEVEL]
                    content = message[P.LOG_CONTENT]
                    if level == P.LOG_LEVEL_INFO:
                        self.factory.send_log_info(content)
                    elif level == P.LOG_LEVEL_ERROR:
                        self.factory.send_log_error(content)

            elif self.client_type == P.CLIENT_ADMIN:
                room_id = message[P.ROOM_ID]

                if message[P.MESSAGE_TYPE] == P.MESSAGE_TYPE_RUN:
                    self.factory.process_run_room(room_id)
                elif message[P.MESSAGE_TYPE] == P.MESSAGE_TYPE_HALT:
                    self.factory.process_halt_room(room_id)
                elif message[P.MESSAGE_TYPE] == P.MESSAGE_TYPE_RESET:
                    self.factory.process_reset_room(room_id)
                elif message[P.MESSAGE_TYPE] == P.MESSAGE_TYPE_SEND_EVENT_TO:
                    node = message[P.SEND_EVENT_NODE]
                    event_to_send = message[P.EVENT]
                    self.factory.process_send_event_to(room_id, node, event_to_send)
                elif message[P.MESSAGE_TYPE] == P.MESSAGE_TYPE_SEND_EVENT_AS:
                    node = message[P.SEND_EVENT_NODE]
                    event_to_send = message[P.EVENT]
                    self.factory.process_send_event_as(room_id, node, event_to_send)
                elif message[P.MESSAGE_TYPE] == P.MESSAGE_TYPE_PRESSED_ADMIN_BUTTON:
                    button_id = message[P.PRESSED_BUTTON_ID]
                    self.factory.process_on_admin_button_pressed(room_id, button_id)

            else:
                self.process_i_am_message(message)

    def validate_message(self, message):
        try:
            message_type = message[P.MESSAGE_TYPE]
        except KeyError:
            return False, "Message has no type"

        if not self.client_type:
            if message_type != P.MESSAGE_TYPE_I_AM:
                return False, "Client type is not yet declared"

            if P.I_AM_CLIENT_TYPE not in message:
                return False, "Missing client type argument"

            if message[P.I_AM_CLIENT_TYPE] not in P.CLIENT_TYPES:
                return False, "Unknown client type"

            if message[P.I_AM_CLIENT_TYPE] == P.CLIENT_NODE:
                if P.I_AM_NAME not in message:
                    return False, "Missing name argument"

                if not validate_node_name(message[P.I_AM_NAME]):
                    return False, "Name must be alphanumeric"

                if P.I_AM_CHANNEL not in message:
                    return False, "Missing channel argument"

                if not validate_channel(message[P.I_AM_CHANNEL]):
                    return False, "Channel must be alphanumeric"
        else:
            if self.client_type == P.CLIENT_NODE:
                if message_type == P.MESSAGE_TYPE_LOG:
                    if P.LOG_LEVEL not in message:
                        return False, "Missing log level argument"

                    log_levels = [P.LOG_LEVEL_INFO, P.LOG_LEVEL_ERROR]
                    if message[P.LOG_LEVEL] not in log_levels:
                        return False, "Expecting a log level in {}".format(", ".join(log_levels))

                    if P.LOG_CONTENT not in message:
                        return False, "Missing content argument"

                elif message_type != P.MESSAGE_TYPE_EVENT:
                    return False, "Expecting an event message"

            elif self.client_type == P.CLIENT_ADMIN:
                if message_type not in P.HANDLED_ADMIN_MESSAGE_TYPES:
                    return False, "Expecting a message type in {}".format(
                        ", ".join(P.HANDLED_ADMIN_MESSAGE_TYPES))

                if P.ROOM_ID not in message:
                    return False, "Message has no room id"

                if message_type in [P.MESSAGE_TYPE_SEND_EVENT_TO, P.MESSAGE_TYPE_SEND_EVENT_AS]:
                    if P.EVENT not in message:
                        return False, "Missing event argument"

                    if P.SEND_EVENT_NODE not in message:
                        return False, "Missing node argument"

                if message_type == P.MESSAGE_TYPE_PRESSED_ADMIN_BUTTON:
                    if P.PRESSED_BUTTON_ID not in message:
                        return False, "Missing button_id argument"

        return True, None

    def log_message(self, message, to_server=True):
        # TODO: think of a more efficient way to achieve this
        pass
        # body = ""
        # if not self.client_type:
        #     identifier = self.peer
        #
        #     body = {
        #         P.I_AM_CLIENT_TYPE: message[P.I_AM_CLIENT_TYPE],
        #         P.I_AM_NAME: message.get(P.I_AM_NAME, ""),
        #         P.I_AM_CHANNEL: message.get(P.I_AM_CHANNEL, ""),
        #     }
        #
        # else:
        #     if self.client_type == P.CLIENT_ADMIN:
        #         at = message[P.ROOM_ID]
        #
        #         if message[P.MESSAGE_TYPE] == P.MESSAGE_TYPE_TIC_TAC:
        #             body = message[P.TIC_TAC_TICKS]
        #         elif message[P.MESSAGE_TYPE] == P.MESSAGE_TYPE_RECORD:
        #             body = {
        #                 P.RECORD_ID: message[P.RECORD_ID],
        #                 P.RECORD_TICKS: message[P.RECORD_TICKS],
        #                 P.RECORD_LABEL: message[P.RECORD_LABEL],
        #             }
        #         elif message[P.MESSAGE_TYPE] in [P.MESSAGE_TYPE_SEND_EVENT_TO, P.MESSAGE_TYPE_SEND_EVENT_AS]:
        #             body = {
        #                 P.SEND_EVENT_NODE: message[P.SEND_EVENT_NODE],
        #                 P.EVENT: message[P.EVENT],
        #             }
        #
        #     else:
        #         at = self.channel
        #         body = message[P.EVENT]
        #
        #     identifier = "{}@{}".format(self.name, at)
        #
        # if to_server:
        #     from_ = identifier
        #     to = "$server"
        # else:
        #     from_ = "$server"
        #     to = identifier
        #
        # type_ = message[P.MESSAGE_TYPE]
        #
        # log = "[{} > {}] {}".format(from_, to, type_)
        # if body:
        #     log += " {}".format(body)
        #
        # logger.info(log)

    def process_i_am_message(self, message):
        # P.CLIENT_NODE or P.CLIENT_ADMIN, thanks to validate_message
        self.client_type = message[P.I_AM_CLIENT_TYPE]

        if message[P.I_AM_CLIENT_TYPE] == P.CLIENT_NODE:
            self.name = message[P.I_AM_NAME]
            self.channel = message[P.I_AM_CHANNEL]
            self.factory.register_node(self)
        else:
            self.name = P.CLIENT_ADMIN
            self.factory.register_admin(self)

    def send_event(self, event):
        message = {
            P.MESSAGE_TYPE: P.MESSAGE_TYPE_EVENT,
            P.EVENT: event,
        }
        self.send_json(message)

    def send_log_info(self, content):
        self.send_log(P.LOG_LEVEL_INFO, content)

    def send_log_error(self, content):
        self.send_log(P.LOG_LEVEL_ERROR, content)

    def send_log(self, level, content):
        message = {
            P.MESSAGE_TYPE: P.MESSAGE_TYPE_LOG,
            P.LOG_LEVEL: level,
            P.LOG_CONTENT: content,
        }
        self.send_json(message)

    def send_notification(self, type_, message):
        message_to_send = {
            P.MESSAGE_TYPE: P.MESSAGE_TYPE_NOTIFICATION,
            P.NOTIFICATION_TYPE: type_,
            P.NOTIFICATION_MESSAGE: message,
        }
        self.send_json(message_to_send)

    def send_tic_tac(self, room_id, session_time):
        message = {
            P.ROOM_ID: room_id,
            P.MESSAGE_TYPE: P.MESSAGE_TYPE_TIC_TAC,
            P.TIC_TAC_SESSION_TIME: session_time,
        }
        self.send_json(message)

    def send_record(self, room_id, record_id, session_time, label):
        message = {
            P.ROOM_ID: room_id,
            P.MESSAGE_TYPE: P.MESSAGE_TYPE_RECORD,
            P.RECORD_ID: record_id,
            P.RECORD_SESSION_TIME: session_time,
            P.RECORD_LABEL: label,
        }
        self.send_json(message)

    def send_reset(self, room_id):
        message = {
            P.ROOM_ID: room_id,
            P.MESSAGE_TYPE: P.MESSAGE_TYPE_RESET,
        }
        self.send_json(message)

    def send_live_data(self, room_id, session_time, records):
        message = {
            P.MESSAGE_TYPE: P.MESSAGE_TYPE_INIT_LIVE_DATA,
            P.ROOM_ID: room_id,
            P.RECORD_SESSION_TIME: session_time,
            P.INIT_LIVE_DATA_RECORDS: records,
        }
        self.send_json(message)

    def send_json(self, dict_):
        unicode_json = json.dumps(dict_, ensure_ascii=False)
        bytes_ = unicode_json.encode("utf8")

        logger.debug("Sending {}".format(dict_))
        self.log_message(dict_, to_server=False)
        self.sendMessage(bytes_)
