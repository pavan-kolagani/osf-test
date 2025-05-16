from shiny import ui
from shinyswatch import theme

app_ui = ui.page_fluid(
    ui.panel_title("OSF Integration"),
    ui.output_ui("login_button_ui"),
    ui.output_ui("main_ui"), 
    theme=theme.flatly
)



