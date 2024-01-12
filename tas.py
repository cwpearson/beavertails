from enum import Enum

from pulp import LpProblem, LpMinimize, lpSum, LpVariable, value


class Item(Enum):
    BEAVER = 0
    LOG = 1
    PLANK = 2
    WATER = 3
    BIOFUEL = 4
    POTATO = 5
    POTATO_CROP = 6
    PLANT_TREE = 7
    TREE_OAK = 8
    BOT = 9
    BOT_CHASIS = 10
    BOT_HEAD = 11
    BOT_ARM = 12
    METAL_BLOCK = 13
    GEAR = 14
    SCRAP_METAL = 15
    TREATED_PLANK = 16
    RESIN = 17
    POWER = 18
    TREE_PINE_RESIN = 19
    CARROT = 20
    CARROT_CROP = 21


class Rates:
    def __init__(self, rates):
        self.rates = rates

    def __getitem__(self, key):
        return self.rates.get(key, 0)

    def items(self):
        return self.rates.items()

    def __iadd__(self, rhs):
        for key, val in rhs.rates.items():
            self.rates[key] = self.rates.get(key, 0) + val
        return self

    def __isub__(self, rhs):
        for key, val in rhs.rates.items():
            self.rates[key] = self.rates.get(key, 0) - val
        return self

    def __repr__(self):
        return repr(self.rates)

    def get(self, key, default):
        return self.rates.get(key, default)


class Recipe:
    def __init__(self, name, tiles, inputs=Rates({}), outputs=Rates({}), workers=0):
        self.name = name
        self.tiles = tiles
        self.inputs = inputs
        self.outputs = outputs
        self.workers = workers

    def __repr__(self):
        return self.name


FARMHOUSE_RATE = 16  # FIXME: made up. Different rates for different foods?
LUMBERJACK_RATE = 16  # FIXME: made up
FORESTER_RATE = 16  # FIXME: made up
SCAVENGER_RATE = 16  # FIXME: made up
TAPPER_RATE = 16  # FIXME: made up

RECIPES = [
    Recipe(
        "Lodge (eat Carrots)",
        4,
        inputs=Rates({Item.WATER: 3 * 2.25 / 24, Item.CARROT: 3 * 2.75 / 24}),
        outputs=Rates({Item.BEAVER: 3}),
    ),
    Recipe(
        "Forester", 4, outputs=Rates({Item.PLANT_TREE: FORESTER_RATE / 24}), workers=1
    ),
    Recipe(
        "Lumberjack (Oak)",
        1,
        inputs=Rates({Item.BEAVER: 1, Item.TREE_OAK: LUMBERJACK_RATE / 24}),
        outputs=Rates({Item.LOG: 8 * LUMBERJACK_RATE / 24}),
    ),
    Recipe(
        "Oak (logs)",
        1,
        inputs=Rates({Item.PLANT_TREE: 1 / 24 / 30}),
        outputs=Rates({Item.TREE_OAK: 8 / 24 / 30}),
    ),
    Recipe(
        "Pine (resin)",
        1,
        outputs=Rates({Item.TREE_PINE_RESIN: 2 / 24 / 7}),
    ),
    Recipe(
        "Lumber Mill",
        6,
        inputs=Rates({Item.BEAVER: 1, Item.LOG: 1 / 1.3, Item.POWER: 50}),
        outputs=Rates({Item.PLANK: 1 / 1.3}),
    ),
    Recipe(
        "Refinery (Potato)",
        6,
        inputs=Rates({Item.BEAVER: 2, Item.WATER: 2 / 3, Item.POTATO: 2 / 3}),
        outputs=Rates({Item.BIOFUEL: 30 / 3}),
    ),
    Recipe(
        "Potato (Crop)",
        1,
        outputs=Rates({Item.POTATO_CROP: 1 / 24 / 6}),
    ),
    Recipe(
        "Carrot (Crop)",
        1,
        outputs=Rates({Item.CARROT_CROP: 3 / 24 / 4}),
    ),
    Recipe(
        "Water Pump",
        4,
        inputs=Rates({Item.BEAVER: 1}),
        outputs=Rates({Item.WATER: 1 / 0.33}),
    ),
    Recipe(
        "Farmhouse (Potato)",
        4,
        inputs=Rates({Item.BEAVER: 3, Item.POTATO_CROP: FARMHOUSE_RATE / 24}),
        outputs=Rates({Item.POTATO: FARMHOUSE_RATE / 24}),
    ),
    Recipe(
        "Farmhouse (Carrot)",
        4,
        inputs=Rates({Item.BEAVER: 3, Item.CARROT_CROP: 3 * FARMHOUSE_RATE / 24}),
        outputs=Rates({Item.CARROT: 3 * FARMHOUSE_RATE / 24}),
    ),
    Recipe(
        "Bot Assembler",
        9,
        inputs=Rates(
            {
                Item.BEAVER: 2,
                Item.BOT_CHASIS: 1 / 72,
                Item.BOT_ARM: 4 / 72,
                Item.BOT_HEAD: 1 / 72,
                Item.POWER: 250,
            }
        ),
        outputs=Rates({Item.BOT: 1 / 72}),
    ),
    Recipe(
        "Bot Part Factory (chasis)",
        9,
        inputs=Rates(
            {
                Item.BEAVER: 2,
                Item.PLANK: 5 / 18,
                Item.BIOFUEL: 1 / 18,
                Item.METAL_BLOCK: 1 / 18,
                Item.POWER: 150,
            }
        ),
        outputs=Rates({Item.BOT_CHASIS: 1 / 18}),
    ),
    Recipe(
        "Bot Part Factory (head)",
        9,
        inputs=Rates(
            {
                Item.BEAVER: 2,
                Item.PLANK: 1 / 18,
                Item.GEAR: 3 / 18,
                Item.METAL_BLOCK: 1 / 18,
                Item.POWER: 150,
            }
        ),
        outputs=Rates({Item.BOT_HEAD: 1 / 18}),
    ),
    Recipe(
        "Bot Part Factory (arm)",
        9,
        inputs=Rates(
            {
                Item.BEAVER: 2,
                Item.PLANK: 1 / 4.5,
                Item.GEAR: 3 / 4.5,
                Item.POWER: 150,
            }
        ),
        outputs=Rates({Item.BOT_ARM: 1 / 4.5}),
    ),
    Recipe(
        "Gear Workshop",
        6,
        inputs=Rates({Item.BEAVER: 1, Item.PLANK: 1 / 3, Item.POWER: 120}),
        outputs=Rates({Item.GEAR: 1 / 3}),
    ),
    Recipe(
        "Smelter",
        8,
        inputs=Rates(
            {
                Item.BEAVER: 1,
                Item.SCRAP_METAL: 2 / 4,
                Item.LOG: 0.2 / 4,
                Item.POWER: 200,
            }
        ),
        outputs=Rates({Item.METAL_BLOCK: 1 / 4}),
    ),
    Recipe(
        "Mine (Scrap Metal)",
        25,
        inputs=Rates(
            {Item.BEAVER: 10, Item.TREATED_PLANK: 1 / 1.8, Item.GEAR: 1 / 1.8}
        ),
        outputs=Rates({Item.SCRAP_METAL: 2 / 1.8}),
    ),
    Recipe(
        "Wood workshop",
        8,
        inputs=Rates(
            {Item.BEAVER: 1, Item.PLANK: 1 / 3, Item.RESIN: 1 / 3, Item.POWER: 250}
        ),
        outputs=Rates({Item.TREATED_PLANK: 1 / 3}),
    ),
    Recipe(
        "Tapper's Shack (Resin)",
        4,
        inputs=Rates({Item.BEAVER: 1, Item.TREE_PINE_RESIN: TAPPER_RATE / 24}),
        outputs=Rates({Item.RESIN: TAPPER_RATE / 24}),
    ),
    Recipe(
        "Water Wheel",
        3,
        outputs=Rates({Item.POWER: 200}),
    ),
]


def construct_phase1(needs: Rates):
    item_ids = dict((item, i) for i, item in enumerate(Item))
    recipe_ids = dict((recipe, i) for i, recipe in enumerate(RECIPES))

    # print(item_ids)
    # print(recipe_ids)

    prob = LpProblem("phase1", LpMinimize)

    # number of each recipe used, must be integer
    recipe_counts = []
    for recipe in RECIPES:
        var = LpVariable(recipe.name, 0, cat="Integer")
        recipe_counts += [var]

    # how much each item is being produced
    # require that the net rate of production for each item is at least 0 (no negative items)
    item_rates = []
    for item in Item:
        item_rate = lpSum(
            recipe.outputs[item] * recipe_counts[ri]
            - recipe.inputs[item] * recipe_counts[ri]
            for recipe, ri in recipe_ids.items()
        )
        prob += item_rate >= 0
        item_rates += [item_rate]

    # want to minimize the number of beavers
    beaver_count = 0
    for ri, count in enumerate(recipe_counts):
        beaver_count += RECIPES[ri].inputs.get(Item.BEAVER, 0) * count
    prob += beaver_count

    # require that particular item rates meet our needs
    for item, per_hour in needs.items():
        prob += item_rates[item_ids[item]] >= per_hour

    # print(prob)

    return prob


def construct_phase2(needs: Rates, workers):
    item_ids = dict((item, i) for i, item in enumerate(Item))
    recipe_ids = dict((recipe, i) for i, recipe in enumerate(RECIPES))

    # print(item_ids)
    # print(recipe_ids)

    prob = LpProblem("phase2", LpMinimize)

    # number of each recipe used, must be integer
    recipe_counts = []
    for recipe in RECIPES:
        var = LpVariable(recipe.name, 0, cat="Integer")
        recipe_counts += [var]

    # how much each item is being produced
    item_rates = []
    for item in Item:
        item_rate = lpSum(
            recipe.outputs[item] * recipe_counts[ri]
            - recipe.inputs[item] * recipe_counts[ri]
            for recipe, ri in recipe_ids.items()
        )
        prob += item_rate >= 0
        item_rates += [item_rate]

    # require the known optimal number of beavers
    beaver_count = 0
    for ri, count in enumerate(recipe_counts):
        beaver_count += RECIPES[ri].inputs.get(Item.BEAVER, 0) * count
    prob += beaver_count <= workers

    # minimize tiles used
    prob += lpSum(RECIPES[ri].tiles * count for ri, count in enumerate(recipe_counts))

    # require that particular item rates meet our needs
    for item, per_hour in needs.items():
        prob += item_rates[item_ids[item]] >= per_hour

    print(prob)

    return prob


if __name__ == "__main__":
    needs = Rates({Item.BOT: 1 / 24})

    prob1 = construct_phase1(needs)

    status1 = prob1.solve()
    # for var in prob1.variables():
    #     print(var, value(var))

    # run again, constraining to the minimum number of beavers
    print("=========================")
    print("beavers:", value(prob1.objective))
    prob2 = construct_phase2(needs, value(prob1.objective))

    status2 = prob2.solve()
    for var in prob1.variables():
        print(var, value(var))
    for var in prob2.variables():
        print(var, value(var))

    print("beavers:", value(prob1.objective))
    print("tiles:  ", value(prob2.objective))
