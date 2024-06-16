class TextWithProperties:
    text: str
    properties: dict[str, str | int]

    def __init__(self, text: str, properties: dict[str, str | int]):
        self.text = text
        self.properties = properties
