from enum import Enum
from pathlib import Path
import json

from pulp import LpProblem, LpMinimize, lpSum, LpVariable, value

THIS_DIR = Path(__file__).parent.absolute()

# create Items enum
with open(THIS_DIR / "static" / "items.json") as f:
    data = json.load(f)
    Item = Enum("Items", data)


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

    def __repr__(self):
        return self.name


def recipe_from_dict(d: dict) -> Recipe:
    """convert a dict to a Recipe.
    BEAVER and POWER are already a rate, so don't divide by time"""

    def numeric(o):
        if isinstance(o, str):
            return eval(o)
        return o

    r_inputs = {}
    for k, v in d.get("inputs", {}).items():
        if k in ("BEAVER", "POWER"):
            r_inputs[Item[k]] = numeric(v)
        else:
            r_inputs[Item[k]] = numeric(v) / numeric(d["period"])
    r_outputs = {}
    for k, v in d.get("outputs", {}).items():
        if k in ("BEAVER", "POWER"):
            r_outputs[Item[k]] = numeric(v)
        else:
            r_outputs[Item[k]] = numeric(v) / numeric(d["period"])

    return Recipe(
        d["name"], int(d["tiles"]), inputs=Rates(r_inputs), outputs=Rates(r_outputs)
    )


FARMHOUSE_PERIOD = 24 / 16  # FIXME: made up. Different rates for different foods?
LUMBERJACK_PERIOD = 24 / 16  # FIXME: made up
FORESTER_PERIOD = 24 / 16  # FIXME: made up
SCAVENGER_RATE = 16  # FIXME: made up
TAPPER_RATE = 16  # FIXME: made up

RECIPES = [
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
]

# load additional recipes
with open(THIS_DIR / "static" / "recipes.json") as f:
    data = json.load(f)
    for d in data:
        RECIPES += [recipe_from_dict(d)]

ITEM_IDS = dict((item, i) for i, item in enumerate(Item))
RECIPE_IDS = dict((recipe, i) for i, recipe in enumerate(RECIPES))


def make_problem_constraints(name: str, needs: Rates):
    prob = LpProblem(name, LpMinimize)

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
            for recipe, ri in RECIPE_IDS.items()
        )
        prob += item_rate >= 0
        item_rates += [item_rate]

    # require that particular item rates meet our needs
    for item, per_hour in needs.items():
        prob += item_rates[ITEM_IDS[item]] >= per_hour

    return prob, recipe_counts


def construct_phase1(needs: Rates):
    prob, recipe_counts = make_problem_constraints("phase1", needs)

    # want to minimize the number of beavers
    beaver_count = 0
    for ri, count in enumerate(recipe_counts):
        beaver_count += RECIPES[ri].inputs.get(Item.BEAVER, 0) * count
    prob += beaver_count

    # print(prob)
    return prob


def construct_phase2(needs: Rates, workers):
    prob, recipe_counts = make_problem_constraints("phase2", needs)

    # require the known optimal number of beavers
    beaver_count = 0
    for ri, count in enumerate(recipe_counts):
        beaver_count += RECIPES[ri].inputs.get(Item.BEAVER, 0) * count
    prob += beaver_count <= workers

    # minimize tiles used
    prob += lpSum(RECIPES[ri].tiles * count for ri, count in enumerate(recipe_counts))

    print(prob)

    return prob


if __name__ == "__main__":
    needs = Rates({Item.BOT: 1 / 24})

    prob1 = construct_phase1(needs)

    print("==== PHASE 1 (optimal beavers) ====")
    status1 = prob1.solve()
    # for var in prob1.variables():
    #     print(var, value(var))
    print("beavers:", value(prob1.objective))

    print("==== PHASE 2 (minimum tiles) ====")
    prob2 = construct_phase2(needs, value(prob1.objective))

    status2 = prob2.solve()
    for var in prob1.variables():
        print(var, value(var))
    for var in prob2.variables():
        print(var, value(var))

    print("beavers:", value(prob1.objective))
    print("tiles:  ", value(prob2.objective))
