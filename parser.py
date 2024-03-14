import json as j
class Parser:
    def __init__(self):
        pass


    def parse_json(self, json, group_title):
        raw = j.loads(json)
        for element in raw['lastScheduleFiles']:
            title = element['title']
            if title == group_title:
                return element['groupCode']
