import json as j
class GroupParser:
    def __init__(self):
        pass


    def getGroupCodeByTitle(self, json, group_title):
        raw = j.loads(json)
        for element in raw['lastScheduleFiles']:
            title = element['title']
            if title == group_title:
                return element['groupCode']
