from group_data import GroupData
class GroupParser:
    def __init__(self):
        pass

    def get_group_code_by_title(self, json, group_title):
        for element in json['lastScheduleFiles']:
            title = element['title']
            if title == group_title:
                return element['groupCode']

    def get_group_codes_list(self, json):
        groupdata_list = list()
        for element in json['lastScheduleFiles']:
            title = element['title']
            code = element['groupCode']
            study_year = element['studyYear']
            groupdata_list.append(GroupData(title, code, study_year))
        return groupdata_list


