from groupdata import GroupData
class GroupParser:
    def __init__(self):
        pass

    #for removal
    def getGroupCodeByTitle(self, json, group_title):
        for element in json['lastScheduleFiles']:
            title = element['title']
            if title == group_title:
                return element['groupCode']



    def getGroupCodesList(self, json):
        groupdata_list = list()
        for element in json['lastScheduleFiles']:
            title = element['title']
            code = element['groupCode']
            study_year = element['studyYear']
            groupdata_list.append(GroupData(title, code, study_year))
        return groupdata_list


