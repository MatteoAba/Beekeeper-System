from collections import OrderedDict
from time import perf_counter

class EventManager:
    _event_queue = OrderedDict()
    _start_timer_event = None

    @staticmethod
    def is_empty_event_queue() -> bool:
        return len(EventManager._event_queue) == 0

    @staticmethod
    def add_event(hive_id: int, polling_time: int) -> None:
        if polling_time not in EventManager._event_queue.keys():
            EventManager._event_queue[polling_time] = []
        
        EventManager._event_queue[polling_time].append(hive_id)

    @staticmethod
    def remove_event(hive_id: int) -> None:
        for key in EventManager._event_queue.keys():
            if hive_id in EventManager._event_queue[key]:
                EventManager._event_queue[key].remove(hive_id)

                # Check if no hives are associated to that key
                if len(EventManager._event_queue[key]) == 0:
                    del EventManager._event_queue[key]
                return

    @staticmethod
    def update_event(hive_id: int, new_polling_time: int) -> None:
        EventManager.remove_event(hive_id=hive_id)
        EventManager.add_event(hive_id=hive_id, polling_time=new_polling_time)

    @staticmethod
    def advance_time(elapsed_seconds: int) -> list:
        new_event_queue = OrderedDict()
        expired_events = []

        # Substract the elapsed seconds from the remaining times and exctract the expired events
        for key in EventManager._event_queue.keys():
            if key - elapsed_seconds <= 0:
                expired_events += EventManager._event_queue[key]
            else:
                new_event_queue[key - elapsed_seconds] = EventManager._event_queue[key]

        EventManager._event_queue = new_event_queue
        return expired_events

    @staticmethod
    def get_next_remaining_time() -> int:
        next_remaining_time = sorted(EventManager._event_queue.keys())[0]
        return next_remaining_time

    @staticmethod
    def start_waiting_time_counter() -> None:
        EventManager._start_timer_event = perf_counter()
    
    @staticmethod
    def stop_waiting_time_counter() -> int:
        elapsed_seconds = round(perf_counter() - EventManager._start_timer_event)
        EventManager._start_timer_event = None
        return elapsed_seconds