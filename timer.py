from datetime import datetime
from time import perf_counter

class Timer(object):
    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, *args):
        self.end = perf_counter()
        self.duration = self.end - self.start

class Time(object):
    @staticmethod
    def get_current_date_time() -> str:
        weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

        return f"{datetime.now().strftime("%Y-%m-%d, %H:%M")}, {weekdays[datetime.now().weekday()]}"