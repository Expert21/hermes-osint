from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, Input, Label, ContentSwitcher, DataTable, Checkbox
from textual.binding import Binding

class HermesApp(App):
    """Hermes OSINT Tool TUI"""

    CSS_PATH = "styles.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("tab", "focus_next", "Next Field"),
        Binding("shift+tab", "focus_previous", "Prev Field"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        with Horizontal(id="main-layout"):
            # Left Sidebar - Form Area
            with Vertical(id="sidebar"):
                yield Static("HERMES", classes="sidebar-title")
                
                # --- Target Info ---
                yield Label("Target Info", classes="section-header")
                
                with Container(classes="form-row"):
                    yield Label("Target", classes="label required")
                    yield Input(placeholder="Target...", id="input-target")
                
                with Container(classes="form-row"):
                    yield Label("Type", classes="label required")
                    yield Input(placeholder="individual/company", id="input-type")
                
                with Container(classes="form-row"):
                    yield Label("Company", classes="label")
                    yield Input(placeholder="Company Name...", id="input-company")

                with Container(classes="form-row"):
                    yield Label("Location", classes="label")
                    yield Input(placeholder="Location...", id="input-location")
                
                with Container(classes="form-row"):
                    yield Label("Email", classes="label")
                    yield Input(placeholder="Email...", id="input-email")
                
                with Container(classes="form-row"):
                    yield Label("Domain", classes="label")
                    yield Input(placeholder="Primary Domain...", id="input-domain")

                with Container(classes="form-row"):
                    yield Label("Add. Domains", classes="label")
                    yield Input(placeholder="Space separated...", id="input-domains")

                # --- Search Options ---
                yield Label("Search Options", classes="section-header")
                
                with Container(classes="form-row"):
                    yield Label("Passive Mode", classes="label")
                    yield Checkbox(id="chk-passive")

                with Container(classes="form-row"):
                    yield Label("No Verify", classes="label")
                    yield Checkbox(id="chk-no-verify")

                with Container(classes="form-row"):
                    yield Label("Skip Search", classes="label")
                    yield Checkbox(id="chk-skip-search")

                with Container(classes="form-row"):
                    yield Label("Skip Social", classes="label")
                    yield Checkbox(id="chk-skip-social")

                # --- Enumeration ---
                yield Label("Enumeration", classes="section-header")

                with Container(classes="form-row"):
                    yield Label("Email Enum", classes="label")
                    yield Checkbox(id="chk-email-enum")

                with Container(classes="form-row"):
                    yield Label("Domain Enum", classes="label")
                    yield Checkbox(id="chk-domain-enum")

                # --- Advanced ---
                yield Label("Advanced", classes="section-header")

                with Container(classes="form-row"):
                    yield Label("JS Render", classes="label")
                    yield Checkbox(id="chk-js-render")

                with Container(classes="form-row"):
                    yield Label("User Vars", classes="label")
                    yield Checkbox(id="chk-username-variations")

                with Container(classes="form-row"):
                    yield Label("Leet Speak", classes="label")
                    yield Checkbox(id="chk-include-leet")

                with Container(classes="form-row"):
                    yield Label("Suffixes", classes="label")
                    yield Checkbox(id="chk-include-suffixes")

                with Container(classes="form-row"):
                    yield Label("No Dedup", classes="label")
                    yield Checkbox(id="chk-no-dedup")

                with Container(classes="form-row"):
                    yield Label("Proxies", classes="label")
                    yield Input(placeholder="Proxy list file...", id="input-proxies")
                
                with Container(classes="form-row"):
                    yield Label("Fetch Proxies", classes="label")
                    yield Checkbox(id="chk-fetch-proxies")

                # --- Configuration ---
                yield Label("Configuration", classes="section-header")

                with Container(classes="form-row"):
                    yield Label("Output", classes="label")
                    yield Input(placeholder="Output file...", id="input-output")

                with Container(classes="form-row"):
                    yield Label("Profile", classes="label")
                    yield Input(placeholder="Config Profile...", id="input-config")

                with Container(classes="form-row"):
                    yield Label("Mode", classes="label")
                    yield Input(placeholder="native/docker", id="input-mode")

                with Container(classes="form-row"):
                    yield Label("Tool", classes="label")
                    yield Input(placeholder="sherlock/theharvester", id="input-tool")

                yield Button("START SCAN", id="btn-start", variant="primary")

            # Right Side - Output & ASCII
            with Vertical(id="right-side"):
                with Container(id="output-area"):
                    yield Static("Output will appear here...", id="output-text")
                
                with Container(id="ascii-area"):
                    yield Static(r"""
   _   _                                  
  | | | | ___ _ __ _ __ ___   ___  ___    
  | |_| |/ _ \ '__| '_ ` _ \ / _ \/ __|   
  |  _  |  __/ |  | | | | | |  __/\__ \   
  |_| |_|\___|_|  |_| |_| |_|\___||___/   
                                          
""", classes="ascii-art")

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-start":
            # Collect Inputs
            target = self.query_one("#input-target").value
            scan_type = self.query_one("#input-type").value
            company = self.query_one("#input-company").value
            location = self.query_one("#input-location").value
            email = self.query_one("#input-email").value
            domain = self.query_one("#input-domain").value
            add_domains = self.query_one("#input-domains").value
            proxies = self.query_one("#input-proxies").value
            output = self.query_one("#input-output").value
            config = self.query_one("#input-config").value
            mode = self.query_one("#input-mode").value
            tool = self.query_one("#input-tool").value

            # Collect Checkboxes
            passive = self.query_one("#chk-passive").value
            no_verify = self.query_one("#chk-no-verify").value
            skip_search = self.query_one("#chk-skip-search").value
            skip_social = self.query_one("#chk-skip-social").value
            email_enum = self.query_one("#chk-email-enum").value
            domain_enum = self.query_one("#chk-domain-enum").value
            js_render = self.query_one("#chk-js-render").value
            user_vars = self.query_one("#chk-username-variations").value
            leet = self.query_one("#chk-include-leet").value
            suffixes = self.query_one("#chk-include-suffixes").value
            no_dedup = self.query_one("#chk-no-dedup").value
            fetch_proxies = self.query_one("#chk-fetch-proxies").value
            
            if not target or not scan_type:
                self.query_one("#output-text").update("[bold red]Error: Target and Type are required![/]")
                return
            
            # Construct Status Message
            status = f"[bold green]Starting Scan...[/]\n"
            status += f"Target: {target} ({scan_type})\n"
            if company: status += f"Company: {company}\n"
            if location: status += f"Location: {location}\n"
            
            status += "\n[bold]Options:[/]\n"
            if passive: status += "- Passive Mode\n"
            if email_enum: status += "- Email Enumeration\n"
            if domain_enum: status += "- Domain Enumeration\n"
            if js_render: status += "- JS Render\n"
            
            self.query_one("#output-text").update(status)

if __name__ == "__main__":
    app = HermesApp()
    app.run()
