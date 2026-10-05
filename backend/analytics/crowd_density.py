class CrowdDensity:

    def __init__(self, low_threshold, medium_threshold):
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold

    def calculate(self, object_counts):

        people = object_counts.get("person", 0)

        if people == 0:
            density = "Empty"
        elif people <= self.low_threshold:
            density = "Low"
        elif people <= self.medium_threshold:
            density = "Medium"
        else:
            density = "High"

        return {
            "people": people,
            "density": density
        }