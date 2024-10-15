from pz.models.new_class_senior import NewClassSeniorModel


class SpecialDeacon:
    deacon: NewClassSeniorModel
    title: str
    order: int

    def __init__(self, deacon: NewClassSeniorModel, title: str, order: int) -> None:
        self.deacon = deacon
        self.title = title
        self.order = order