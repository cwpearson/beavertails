from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, TabbedContent, Label, Input
from textual.validation import Function, Number, ValidationResult, Validator
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual import work

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

    @work(exclusive=True)
    async def run_model(self):
        needs = Rates({})
        for item in Item:
            inp = self.query_one(f"#{item.name}-input")
            rate = float(inp.value)
            if rate != 0:
                needs.rates[item] = rate
        results = solve(needs)
        self.query_one("#results").update(str(results))

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
        with TabbedContent("Tab 1", "Tab 2"):
            yield ItemList()
            yield Label("w00t")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    app = BeavertailsApp()
    app.run()