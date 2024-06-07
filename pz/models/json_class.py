import json


class JSONClass:
    def to_dict(self):
        return {key: value for key, value in vars(self).items() if not key.startswith("_")}

    def __str__(self):
        return self.to_json()

    def to_json(self) -> str:
        # return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4, ensure_ascii=False)
        return json.dumps(self, default=lambda o: o.to_dict(), sort_keys=True, indent=4, ensure_ascii=False)
