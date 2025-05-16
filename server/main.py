from shiny import Inputs, Outputs, Session, render, ui
from server.state import current_user
from server.views import homepage_ui, scholar_dashboard_ui
from server.handlers import login_handler, logout_handler, repo_creation_handler, upload_split_handler, upload_analysis_handler, watch_edit_repo, handle_submit_repo_edit, watch_repo_search
from server.modals import show_repo_modal
from db.models import SessionLocal
from pathlib import Path

def server(input: Inputs, output: Outputs, session: Session):
    db = SessionLocal()

    # wire all effects
    login_handler(input, db)
    logout_handler(input)
    repo_creation_handler(input, db, session)
    show_repo_modal(input, db)
    upload_split_handler(input, db, data_dir=Path("data"))
    upload_analysis_handler(input, db, data_dir=Path(__file__).parent / "data")
    Path("data").mkdir(exist_ok=True)
    watch_edit_repo(input, db)
    handle_submit_repo_edit(input, db)
    watch_repo_search(input)



    @render.ui
    def login_button_ui():
        user = current_user.get()
        if user:
            return ui.input_action_button("logout_btn", "Logout")
        else:
            return ui.input_action_button("login_btn", "Login as Scholar")


    @render.ui
    def main_ui():
        user = current_user.get()
        return scholar_dashboard_ui(db, user) if user else homepage_ui(db)
