from enum import Enum
from pathlib import Path
import json

from pulp import LpProblem, LpMinimize, lpSum, LpVariable, value
from pulp.apis import PULP_CBC_CMD

from beavertails import mypulp

THIS_DIR = Path(__file__).parent.absolute()
STATIC_DIR = THIS_DIR / "static"

# create Items enum
with open(STATIC_DIR / "items.json") as f:
    data = json.load(f)
    Item = Enum("Items", data)


class Rates:
    def __init__(self, rates):
        self.rates = rates

    def __getitem__(self, key):
        return self.rates.get(key, 0)

    def items(self):
        return self.rates.items()

    def __repr__(self):
        return repr(self.rates)

    def get(self, key, default):
        return self.rates.get(key, default)

    def __setitem___(self, key, value):
        self.rates[key] = value


class Settings:
    def __init__(self):
        self.working_hours = 16
        self.efficiency = 0.9
        self.lumberjack_period = 0.75
        self.tapper_period = 0.75
        self.gatherer_period = 0.75
        self.forester_period = 0.75
        self.farmhouse_period = 0.75


class Recipe:
    def __init__(self, name, tiles, inputs=Rates({}), outputs=Rates({}), workers=0):
        self.name = name
        self.tiles = tiles
        self.inputs = inputs
        self.outputs = outputs

    def __repr__(self):
        return self.name


RECIPES = []

# load additional recipes
with open(STATIC_DIR / "recipes.json") as f:
    RECIPES = json.load(f)

ITEM_IDS = dict((item, i) for i, item in enumerate(Item))


def recipe_with_settings(raw_recipe: dict, settings: Settings) -> Recipe:
    """convert a dict to a Recipe.
    BEAVER and POWER are already a rate, so don't divide by time"""

    # numeric() is running eval, and the json
    # recipe definitions are looking for specific variables to be
    # set in this scope.
    scope = locals()

    def numeric(o):
        if isinstance(o, str):
            return eval(
                o,
                None,  # globals
                scope,  # locals
            )
        return o

    r_inputs = {}
    for k, v in raw_recipe.get("inputs", {}).items():
        if k in ("BEAVER", "POWER"):
            r_inputs[Item[k]] = numeric(v)
        else:
            r_inputs[Item[k]] = numeric(v) / numeric(raw_recipe["period"])
    r_outputs = {}
    for k, v in raw_recipe.get("outputs", {}).items():
        if k in ("BEAVER", "POWER"):
            r_outputs[Item[k]] = numeric(v)
        else:
            r_outputs[Item[k]] = numeric(v) / numeric(raw_recipe["period"])

    return Recipe(
        raw_recipe["name"],
        int(raw_recipe["tiles"]),
        inputs=Rates(r_inputs),
        outputs=Rates(r_outputs),
    )


def recipes_with_settings(settings: Settings):
    return [recipe_with_settings(raw_recipe, settings) for raw_recipe in RECIPES]


def make_problem_constraints(name: str, needs: Rates, settings: Settings):
    prob = LpProblem(name, LpMinimize)
    recipes = recipes_with_settings(settings)

    # number of each recipe used, must be integer
    recipe_counts = []
    for recipe in recipes:
        var = LpVariable(recipe.name, 0, cat="Integer")
        recipe_counts += [var]

    # how much each item is being produced
    # require that the net rate of production for each item is at least 0 (no negative items)
    item_rates = []
    for item in Item:
        item_rate = lpSum(
            recipe.outputs[item] * recipe_counts[ri]
            - recipe.inputs[item] * recipe_counts[ri]
            for ri, recipe in enumerate(recipes)
        )
        prob += item_rate >= 0
        item_rates += [item_rate]

    # require that particular item rates meet our needs
    for item, per_hour in needs.items():
        prob += item_rates[ITEM_IDS[item]] >= per_hour

    return prob, recipes, recipe_counts


def construct_phase1(needs: Rates, settings: Settings):
    prob, recipes, recipe_counts = make_problem_constraints("phase1", needs, settings)

    # want to minimize the number of beavers
    beaver_count = 0
    for ri, count in enumerate(recipe_counts):
        beaver_count += recipes[ri].inputs.get(Item.BEAVER, 0) * count
    prob += beaver_count

    # print(prob)
    return prob


def construct_phase2(needs: Rates, settings: Settings, workers: int):
    prob, recipes, recipe_counts = make_problem_constraints("phase2", needs, settings)

    # require the known optimal number of beavers
    beaver_count = 0
    for ri, count in enumerate(recipe_counts):
        beaver_count += recipes[ri].inputs.get(Item.BEAVER, 0) * count
    prob += beaver_count <= workers

    # minimize tiles used
    prob += lpSum(recipes[ri].tiles * count for ri, count in enumerate(recipe_counts))

    print(prob)

    return prob


def solve(needs: Rates, settings: Settings):
    prob1 = construct_phase1(needs, settings)
    status1, log1 = mypulp.solve(prob1)
    prob2 = construct_phase2(needs, settings, value(prob1.objective))
    status2, log2 = mypulp.solve(prob2)

    vars = {var: value(var) for var in prob2.variables()}
    return {
        "beavers": value(prob1.objective),
        "tiles": value(prob2.objective),
        "log": log1 + log2,
        "vars": vars,
    }


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
