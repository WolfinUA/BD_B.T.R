from src.disease_spread.server import Server

if __name__ == '__main__':
    Server.new([
        # 'Lviv Raion',
        # ('Zolochiv Raion, Lviv Oblast', 2),
        # 'Drohobych Raion',
        # ('Sambir Raion', 2),
        'Stryi Raion',
        # 'Chervonohrad Raion',
        # 'Yavoriv Raion'
    ]).launch()
