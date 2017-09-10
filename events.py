import abc


class Event(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.next_event = None

    @abc.abstractmethod
    def serialize(self):
        """Serialize event to json format"""
        pass

    def set_next_event(self, event):
        self.next_event = event


class AddEvent(Event):
    def __init__(self, node_id, root, name):
        super(AddEvent, self).__init__()
        self.id = node_id
        self.root = root
        self.name = name

    def serialize(self):
        return {'event_name': "add", 'event_data': {'name': self.name, 'root': self.root, 'id': self.id}}


class DeleteEvent(Event):
    def __init__(self, node_id):
        super(DeleteEvent, self).__init__()
        self.id = node_id

    def serialize(self):
        return {'event_name': "delete", 'event_data': {'id': self.id}}


class MoveEvent(Event):
    def __init__(self, node_id, root):
        super(MoveEvent, self).__init__()
        self.id = node_id
        self.root = root

    def serialize(self):
        return {'event_name': "move", 'event_data': {'id': self.id, 'root': self.root}}


class EditEvent(Event):
    def __init__(self, node_id, name):
        super(EditEvent, self).__init__()
        self.id = node_id
        self.name = name

    def serialize(self):
        return {'event_name': "edit", 'event_data': {'id': self.id, 'name': self.name}}


class EventsManager:
    def __init__(self):
        self.last_event = self.first_event = None

    def append_event(self, event):
        if self.last_event is None:
            self.last_event = self.first_event = event
        else:
            self.last_event.set_next_event(event)
            self.last_event = event

    def serialize_events(self):
        res = self._serialize_event(self.first_event)
        return res

    def clear(self):
        self.last_event = self.first_event = None

    def _serialize_event(self, event):
        res = dict()
        if event is not None:
            res = event.serialize()
            res['event_next'] = self._serialize_event(event.next_event)
        return res
