from enum import StrEnum


class HumanState(StrEnum):
    Sustainable = 'Sustainable'
    Latent = 'Latent'
    PrimaryTuberculosis = 'Post-Primary Tuberculosis'
    PostPrimaryTuberculosis = 'Primary Tuberculosis'
    Recovered = 'Recovered'
    Death = 'Death'

    def __str__(self):
        return self.name
        # mapping = {
        #     "PostPrimaryTuberculosis": "Post-Primary Tuberculosis",
        #     "PrimaryTuberculosis": "Primary Tuberculosis",
        # }
        # if self.name not in mapping:
        #     return self.name
        # return mapping[self.name]

    @staticmethod
    def all():
        return [
            HumanState.Sustainable,
            HumanState.Latent,
            HumanState.PrimaryTuberculosis,
            HumanState.PostPrimaryTuberculosis,
            HumanState.Recovered,
            HumanState.Death,
        ]

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.name)
