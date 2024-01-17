from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, TabbedContent, Label, Input
from textual.validation import Function, Number, ValidationResult, Validator
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual import work

from textual.message import Message

from beavertails.lib import Item, Rates, solve


class ItemInput(Static):
    def compose(self) -> ComposeResult:
        with VerticalScroll():
            for item in Item:
                with Horizontal(classes="item-input-row"):
                    yield Label(item.name)
                    yield Input(
                        id=f"{item.name}-input",
                        value="0",
                        validators=[Number(minimum=0)],
                    )


class ItemList(Static):
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield ItemInput(classes="item-input")
            yield Label("words words", id="results")

    class ModelLog(Message):
        def __init__(self, log):
            self.log = log
            super().__init__()

    @work(exclusive=True)
    async def run_model(self):
        needs = Rates({})
        for item in Item:
            inp = self.query_one(f"#{item.name}-input")
            rate = float(inp.value)
            if rate != 0:
                needs.rates[item] = rate
        results = solve(needs)
        self.query_one("#results").update(str(results["beavers"]))
        self.post_message(self.ModelLog(results["log"]))

        # raise an event so parent can update log

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        self.run_model()


class BeavertailsApp(App):
    """A Textual app"""

    CSS_PATH = "beavertails.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        with TabbedContent("Tab 1", "Run log"):
            yield ItemList()
            yield Label(id="log")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def on_item_list_model_log(self, message: ItemList.ModelLog) -> None:
        """the names of this function makes textual pick it up as a handler"""
        self.query_one("#log").update(message.log)


if __name__ == "__main__":
    app = BeavertailsApp()
    app.run()
