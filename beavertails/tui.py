from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    Static,
    TabbedContent,
    Label,
    Input,
    Collapsible,
)
from textual.validation import Function, Number, ValidationResult, Validator
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual import work
from textual.reactive import reactive

from textual.message import Message

import beavertails
from beavertails.lib import Item, Rates, solve


class ItemInput(Static):
    def compose(self) -> ComposeResult:
        yield Static("Press Enter after inputting needed item rates")
        with VerticalScroll():
            for item in Item:
                with Horizontal(classes="item-input-row"):
                    yield Label(item.name)
                    yield Input(
                        id=f"{item.name}-input",
                        value="0",
                        validators=[Number(minimum=0)],
                    )
                    yield Label("per hour", classes="item-input-row unit")

    class Needs(Message):
        def __init__(self, data):
            self.data = data
            super().__init__()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """gather up requested needs and post them up"""
        event.stop()  # don't bubble up the changed input event
        if event.validation_result.is_valid:
            data = {}
            for item in Item:
                data[item] = float(self.query_one(f"#{item.name}-input").value)
            self.post_message(ItemInput.Needs(data))


class ItemOutput(Static):
    beavers = reactive(None)
    tiles = reactive(None)
    data = reactive(dict())

    def compose(self) -> ComposeResult:
        yield Label(id="output-beavers")
        yield Label(id="output-tiles")
        with VerticalScroll(id="item-list"):
            yield Label(classes="output-recipe")

    def add_item(self, name, value):
        new_entry = Label(f"{name}: {value}")
        self.query_one("#item-list").mount(new_entry)

    def remove_items(self):
        entries = self.query(".output-recipe")
        for e in entries:
            e.remove()

    def watch_beavers(self, beavers):
        if beavers is not None:
            self.query_one("#output-beavers").update(f"beavers: {beavers}")

    def watch_tiles(self, tiles):
        if self.tiles is not None:
            self.query_one("#output-tiles").update(f"tiles: {tiles}")

    def watch_data(self, data):
        """called when data changes"""
        self.remove_items()
        for name, value in data.items():
            if float(value) > 0:
                self.add_item(name, value)


class ItemList(Static):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield ItemInput(classes="item-input")
            yield ItemOutput(id="results")


class Settings(Static):
    def compose(self) -> ComposeResult:
        with Collapsible(title="Work Building Periods"):
            yield Static(
                "How long does it take this building to do one unit of work (e.g. chop a tree tile)?"
            )
        with VerticalScroll():
            with Horizontal(classes="labeled-setting"):
                yield Label("Farmhouse")
                yield Input(
                    id="farmhouse_period",
                    value="0.75",
                    type="number",
                )
                yield Label("hours", classes="labeled-setting unit")
            with Horizontal(classes="labeled-setting"):
                yield Label("Lumberjack")
                yield Input(
                    id="lumberjack_period",
                    value="0.75",
                    type="number",
                )
                yield Label("hours", classes="labeled-setting unit")
            with Horizontal(classes="labeled-setting"):
                yield Label("Forester")
                yield Input(
                    id="forester_period",
                    value="0.75",
                    type="number",
                )
                yield Label("hours", classes="labeled-setting unit")
            with Horizontal(classes="labeled-setting"):
                yield Label("Scavenger")
                yield Input(
                    id="scavenger_period",
                    value="0.75",
                    type="number",
                )
                yield Label("hours", classes="labeled-setting unit")
            with Horizontal(classes="labeled-setting"):
                yield Label("Tapper")
                yield Input(id="tapper_period", value="0.75", type="number")
                yield Label("hours", classes="labeled-setting unit")
            yield Static("Global Settings")
            # working hours
            with Horizontal(classes="labeled-setting"):
                yield Label("Working Hours")
                yield Input(id="working_hours", value="16", type="integer")
                yield Label("hours", classes="labeled-setting unit")
            # efficiency
            with Horizontal(classes="labeled-setting"):
                yield Label("Efficiency")
                yield Input(id="efficiency", value="0.9", type="number")
                yield Label("", classes="labeled-setting unit")  # takes up space

    class Changed(Message):
        def __init__(self, data):
            self.data = data
            super().__init__()

    def on_input_changed(self, event: Input.Changed) -> None:
        # stop this event from going up
        event.stop()

        # retrieve all settings
        data = {}
        for float_key in [
            "farmhouse_period",
            "lumberjack_period",
            "forester_period",
            "scavenger_period",
            "tapper_period",
            "efficiency",
        ]:
            if event.validation_result.is_valid:
                data[float_key] = float(self.query_one(f"#{float_key}").value)
        for int_key in [
            "working_hours",
        ]:
            if event.validation_result.is_valid:
                data[int_key] = int(self.query_one(f"#{int_key}").value)
        # send them up
        self.post_message(self.Changed(data))


class BeavertailsApp(App):
    """A Textual app"""

    CSS_PATH = "beavertails.tcss"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        with TabbedContent("Input Rates", "Settings", "Solver Log"):
            yield ItemList()
            yield Settings(id="settings")
            yield Label(id="log")

    class ModelLog(Message):
        def __init__(self, log):
            self.log = log
            super().__init__()

    @work(exclusive=True)
    async def run_model(self):
        # construct needs
        needs = Rates({})
        for item, rate in self.needs.items():
            needs.rates[item] = rate

        # construct settings
        settings = beavertails.lib.Settings()
        for key, value in self.settings.items():
            setattr(settings, key, value)
        results = solve(needs, settings)
        # output_dict = dict(results["vars"])
        output_dict = {k: v for k, v in results["vars"].items() if "_int" in str(k)}
        self.query_one("#results").data = output_dict
        self.query_one("#results").beavers = results["beavers"]
        self.query_one("#results").tiles = results["tiles"]
        self.query_one("#log").update(results["log"])

    def on_settings_changed(self, message: Settings.Changed) -> None:
        """capture changed settings"""
        self.settings = message.data

    async def on_item_input_needs(self, message: ItemInput.Needs) -> None:
        """capture changed needs and run the solver"""
        self.needs = message.data
        self.run_model()


if __name__ == "__main__":
    app = BeavertailsApp()
    app.run()
