from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, Input, Label, ContentSwitcher, DataTable
from textual.binding import Binding

class HermesApp(App):
    """Hermes OSINT Tool TUI"""

    CSS_PATH = "styles.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        with Container(id="app-grid"):
            with Vertical(id="sidebar"):
                yield Button("Dashboard", id="btn-dashboard", classes="-active")
                yield Button("Search", id="btn-search")
                yield Button("Social", id="btn-social")
                yield Button("Network", id="btn-network")
                yield Button("Settings", id="btn-settings")
                
            with ContentSwitcher(initial="dashboard", id="main-content"):
                # Dashboard View
                with Vertical(id="dashboard"):
                    yield Static("""
╔═══════════╗
║  ⟨H⟩ERMES ║
╚═══════════╝
""", classes="logo")
                    yield Label("Target Input:")
                    yield Input(placeholder="Enter target username, domain, or email...", id="target-input")
                    yield Button("Start Scan", id="btn-start-scan", variant="primary")
                    yield Static("Ready for operation.", id="status-area")
                
                # Search View
                with Vertical(id="search"):
                    yield Label("Search Engine Modules", classes="section-title")
                    yield DataTable(id="engines-table")
                    
                    yield Label("Add Custom Engine", classes="section-title")
                    with Container(id="add-engine-form"):
                        yield Input(placeholder="Engine Name", id="new-engine-name")
                        yield Input(placeholder="Search URL (use {query} placeholder)", id="new-engine-url")
                        yield Label("CSS Selectors:")
                        yield Input(placeholder="Container Selector", id="sel-container")
                        yield Input(placeholder="Title Selector", id="sel-title")
                        yield Input(placeholder="Link Selector", id="sel-link")
                        yield Input(placeholder="Snippet Selector", id="sel-snippet")
                        yield Button("Add Engine", id="btn-add-engine", variant="success")

                # Social View
                with Vertical(id="social"):
                    yield Label("Social Media Modules")
                    yield Static("Configure social media checks here.")

                # Network View
                with Vertical(id="network"):
                    yield Label("Network Analysis")
                    yield Static("Configure network tools here.")

                # Settings View
                with Vertical(id="settings"):
                    yield Label("Settings")
                    yield Static("Configure application settings here.")

        yield Footer()

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        table = self.query_one(DataTable)
        table.add_columns("Engine", "Status", "Type")
        
        # Load engines from config (mocking for now, ideally import ConfigManager)
        # In a real app, we'd inject ConfigManager
        engines = {
            "DuckDuckGo": True, "Bing": True, "Mojeek": True, "SearxNG": True,
            "PublicWWW": True, "Wayback Machine": True, "Archive.today": True, "Common Crawl": True
        }
        
        for name, enabled in engines.items():
            status = "✅ Enabled" if enabled else "❌ Disabled"
            table.add_row(name, status, "Built-in")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "btn-start-scan":
            target = self.query_one("#target-input").value
            self.query_one("#status-area").update(f"Initiating scan for: {target}...")
            # Logic to trigger scan would go here
            
        elif button_id == "btn-add-engine":
            name = self.query_one("#new-engine-name").value
            url = self.query_one("#new-engine-url").value
            if name and url:
                table = self.query_one(DataTable)
                table.add_row(name, "✅ Enabled", "Custom")
                self.query_one("#new-engine-name").value = ""
                self.query_one("#new-engine-url").value = ""
                # Clear selectors
                self.query_one("#sel-container").value = ""
                self.query_one("#sel-title").value = ""
                self.query_one("#sel-link").value = ""
                self.query_one("#sel-snippet").value = ""
            
        elif button_id in ["btn-dashboard", "btn-search", "btn-social", "btn-network", "btn-settings"]:
            # Handle Navigation
            # Remove active class from all sidebar buttons
            for btn in self.query(Button):
                if btn.id and btn.id.startswith("btn-"):
                    btn.remove_class("-active")
            
            # Add active class to pressed button
            event.button.add_class("-active")
            
            # Switch Content
            view_id = button_id.replace("btn-", "")
            self.query_one(ContentSwitcher).current = view_id

if __name__ == "__main__":
    app = HermesApp()
    app.run()
