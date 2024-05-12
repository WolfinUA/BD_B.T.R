class RandomPoint:
    @staticmethod
    def single(geo_df):
        rows = geo_df.sample(n=1).iloc
        return rows[0].representative_point

    @staticmethod
    def multiple(geo_df, amount):
        return list(geo_df.sample(n=amount)['representative_point'])