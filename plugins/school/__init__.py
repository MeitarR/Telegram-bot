from plugins.school import timetable

__commands__ = {'timetable': timetable.timetable_cmd}
__callbacks__ = {'/timetable': timetable.timetable_callback}
__all__ = ['timetable']
