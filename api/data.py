

class DataProvider(object):
    """Reads data from the yaml files."""
    def __init__(self):
        self.RESOURCES = ['courses', 'sections', 'subjects', 'instructors']

        for attr in self.RESOURCES:
            setattr(self, attr, {})
        self.read_files()

    def read_files(self):
        # mock some data
        self.courses = {
            "ANAT100": {
                "id": "ANAT100",
                "data": "sample data for ANAT100"
            },
            "ANAT200": {
                "id": "ANAT200",
                "data": "More!!! sample data for ANAT200"
            }
        }
        pass

    def get_list(self, resource):
        if hasattr(self, resource):
            return getattr(self, resource).values()
        return None

    def get_item(self, resource, uid):
        if hasattr(self, resource):
            r_dict = getattr(self, resource)
            if uid in r_dict:
                return r_dict[uid]
        return None

data_provider = DataProvider()
