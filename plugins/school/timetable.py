import urllib.request
import lxml.html as lh
import collections
import datetime

Lesson = collections.namedtuple('Lesson', 'subject teacher room')
Hour = collections.namedtuple('Hour', 'number lessons')
Day = collections.namedtuple('Day', 'number name hours')

days_of_week = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]


def get_updates():
    url = "https://www.webtop.co.il/mobile/superSchool.aspx?institutionCode=440545&classNum=52&view=timetable&platform="

    req = urllib.request.Request(
        url,
        data=None,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3)'
                          ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
    )
    f = urllib.request.urlopen(req)
    content = f.read()

    root = lh.fromstring(content)

    ans = []
    counter = 0
    for day in root.xpath("//div[contains(@class, 'weekday')]"):
        hours = []
        for tr in day.findall('.//tr'):
            empty_tds = tr.xpath('td')
            for empty_td in empty_tds:
                if hasattr(empty_td, 'text') and empty_td.text == " ":
                    tr.remove(empty_td)
            if tr.find('td') is not None:
                if tr.find('td[@style="font-size:14px"]') is not None and len(tr.findall('td')) == 2:
                    hour_num_td, data_td = tr.findall('td')
                    lessons = []
                    temp_less = Lesson(None, None, None)
                    for thing in data_td:
                        if thing.tag == 'span':
                            if thing.get('class', '') == 'subject':
                                temp_less = temp_less._replace(subject=thing.text)
                            elif thing.get('class', '') == 'teacher':
                                temp_less = temp_less._replace(teacher=thing.text)
                            elif thing.get('class', '') == 'room':
                                temp_less = temp_less._replace(room=thing.text)
                        elif thing.tag == 'hr':
                            lessons.append(temp_less)
                            temp_less = Lesson(None, None, None)
                    lessons.append(temp_less)

                    hour = Hour(number=hour_num_td.text, lessons=lessons)
                    hours.append(hour)
        ans.append(Day(number=counter, name=days_of_week[counter], hours=hours))
        counter += 1
    return ans


def get_timetable_of_day(day_number):
    all_timetables = get_updates()
    try:
        return all_timetables[day_number]
    except IndexError:
        return None


def get_today_timetable():
    return get_timetable_of_day((datetime.datetime.today().weekday() + 1) % 7)


def get_tomorrow_timetable():
    return get_timetable_of_day((datetime.datetime.today().weekday() + 2) % 7)


def to_string(day):
    if day is None:
        return "היום לא קיים במערכת..."
    full_msg = "מערכת ליום " + day.name + ":\n\n"
    for hour in day.hours:
        full_msg += "\nשיעור " + str(hour.number) + ":\n"
        for lesson in hour.lessons:
            full_msg += lesson.subject + ' עם ' + lesson.teacher + ' (' + str(lesson.room) + ')\n'
    return full_msg

if __name__ == "__main__":
    aaa = get_updates()
    print(to_string(get_tomorrow_timetable()))
