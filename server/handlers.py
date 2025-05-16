import logging
from pathlib import Path

log_path = Path(__file__).resolve().parent / "debug_modal_state.log"

logger = logging.getLogger("app_debug")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.FileHandler(str(log_path), mode="a", encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


logger.debug("Logger initialized and flushed.")
handler.flush()

print(f"Logger setup complete at: {log_path}")

from shiny import reactive, ui
from db.models import Repository, User, Dataset, VisibilityEnum
from .state import *
from pathlib import Path
import pandas as pd
from utils.split import split_dataset
import pyreadr
import shutil


def login_handler(input, db):
    @reactive.effect
    @reactive.event(input.login_btn)
    def _show_login():
        ui.modal_show(
            ui.modal(
                ui.input_text("username", "Username"),
                ui.input_password("password", "Password"),
                ui.input_action_button("submit_login", "Login"),
                title="Login",
                easy_close=True
            )
        )

    @reactive.effect
    @reactive.event(input.submit_login)
    def _submit_login():
        user = db.query(User).filter_by(
            username=input.username(),
            password_hash=input.password()
        ).one_or_none()
        if user and user.role == "scholar":
            current_user.set(user)
            ui.modal_remove()
            ui.notification_show("Login successful", type="message")
        else:
            ui.notification_show("Invalid login", type="error")

def repo_creation_handler(input, db, session):
    @reactive.effect
    @reactive.event(input.create_repo)
    def _():
        ui.modal_show(
            ui.modal(
                ui.input_text("new_repo_name", "Repository Name"),
                ui.input_text("new_repo_description", "Description"),
                ui.input_select("new_repo_visibility", "Visibility", {
                    "PRIVATE": "Private",
                    "EMBARGOED": "Embargoed",
                    "PUBLIC": "Public"
                }),
                ui.input_text("split_column", "Column to Stratify Split On (optional)"),
                ui.input_select("split_ratio", "Split Ratio", {
                    "0.7,0.15,0.15": "70/15/15",
                    "0.6,0.2,0.2": "60/20/20",
                    "0.8,0.1,0.1": "80/10/10"
                }),
                ui.input_file("dataset_file", "Upload Dataset (.rda or .rds)", accept=[".rds", ".rda"]),
                ui.input_action_button("submit_new_repo", "Create"),
                title="Create Repository",
                easy_close=True
            )
        )

    @reactive.effect
    @reactive.event(input.submit_new_repo)
    def _():
        user = current_user.get()
        if not user:
            ui.notification_show("Login required", type="error")
            return

        file_info = input.dataset_file()
        if file_info is None or len(file_info) == 0:
            ui.notification_show("Please upload a valid dataset file.", type="error")
            return

        file_path = Path(file_info[0]["datapath"])
        split_col = input.split_column()
        ratio = tuple(map(float, input.split_ratio().split(",")))

        try:
            result = pyreadr.read_r(str(file_path))
            df = next(iter(result.values()))  # Read the first object in the file
        except Exception as e:
            ui.notification_show(f"Failed to load dataset: {e}", type="error")
            return

        try:
            df_train, df_test, df_val = split_dataset(df, split_col, ratio)
        except Exception as e:
            ui.notification_show(f"Error during split: {e}", type="error")
            return

        new_repo = Repository(
            user_id=user.id,
            repo_name=input.new_repo_name(),
            description=input.new_repo_description(),
            visibility=VisibilityEnum[input.new_repo_visibility()]
        )
        db.add(new_repo)
        db.commit()
        db.refresh(new_repo)

        # Save files
        repo_dir = Path("data") / user.username / new_repo.repo_name
        repo_dir.mkdir(parents=True, exist_ok=True)
        df_train.to_csv(repo_dir / "train.csv", index=False)
        df_test.to_csv(repo_dir / "test.csv", index=False)
        df_val.to_csv(repo_dir / "validation.csv", index=False)

        db.add_all([
            Dataset(repository_id=new_repo.id, dataset_type="train", location=str(repo_dir / "train.csv")),
            Dataset(repository_id=new_repo.id, dataset_type="test", location=str(repo_dir / "test.csv")),
            Dataset(repository_id=new_repo.id, dataset_type="validation", location=str(repo_dir / "validation.csv")),
        ])
        db.commit()

        ui.modal_remove()
        ui.notification_show("Repository created and dataset split.", type="message")


def logout_handler(input):
    @reactive.effect
    @reactive.event(input.logout_btn)
    def _logout():
        print("[LOGOUT] Logout triggered")
        reset_app_state()
        logger.debug("[LOGOUT] Resetting all reactive state variables")
        ui.modal_remove()
        ui.notification_show("You have been logged out.", type="message")
def upload_split_handler(input, db, data_dir):
    import re
    from shiny import reactive, ui

    @reactive.effect
    def _watch_upload_clicks():
        for repo in db.query(Repository).all():
            btn_id = f"upload_dataset_{repo.id}"
            if hasattr(input, btn_id) and input[btn_id]() > 0:
                logger.debug(f"[MODAL] Triggered by {btn_id}, setting selected_repo_id={repo.id}")
                selected_repo_id.set(repo.id)
                ui.modal_show(
                    ui.modal(
                        ui.input_file("uploaded_csv", "Upload CSV", accept=[".csv"]),
                        ui.input_select("split_ratio", "Split Ratio", {
                            "0.7-0.15-0.15": "70/15/15",
                            "0.6-0.2-0.2": "60/20/20",
                            "0.8-0.1-0.1": "80/10/10"
                        }),
                        ui.input_text("split_column", "Optional: Column to Stratify By"),
                        ui.input_action_button("submit_split", "Split & Save"),
                        title=f"Upload and Split Dataset for {repo.repo_name}",
                        easy_close=True
                    )
                )

    @reactive.effect
    @reactive.event(input.submit_split)
    def _handle_split():
        from utils.split import split_dataset
        import pandas as pd
        from pathlib import Path

        file_info = input.uploaded_csv()
        if not file_info:
            ui.notification_show("No file uploaded.", type="error")
            return

        user = current_user.get()
        repo_id = selected_repo_id.get()
        if not (user and repo_id):
            ui.notification_show("Session invalid.", type="error")
            return

        repo = db.query(db.models.Repository).filter_by(id=repo_id).first()
        if not repo:
            ui.notification_show("Repo not found.", type="error")
            return

        ratio = tuple(map(float, input.split_ratio().split("-")))
        split_col = input.split_column().strip() or None
        df = pd.read_csv(file_info[0]["datapath"])

        try:
            df_train, df_test, df_val = split_dataset(df, split_col, ratio)
        except Exception as e:
            ui.notification_show(f"Split failed: {e}", type="error")
            return

        repo_path = Path(data_dir) / user.username / repo.repo_name
        repo_path.mkdir(parents=True, exist_ok=True)

        df_train.to_csv(repo_path / "train.csv", index=False)
        df_test.to_csv(repo_path / "test.csv", index=False)
        df_val.to_csv(repo_path / "validation.csv", index=False)

        ui.modal_remove()
        ui.notification_show("Dataset split and saved.", type="message")

def upload_analysis_handler(input, db, data_dir):
    @reactive.effect
    def _watch_upload_clicks():
        user = current_user.get()
        if not user:
            return

        for repo in db.query(user.__class__).get(user.id).repositories:
            btn_id = f"upload_analysis_{repo.id}"
            try:
                if input[btn_id]() > 0 and btn_id not in handled_clicks.get():
                    logger.debug(f"[MODAL] Triggered by {btn_id}, setting selected_repo_id={repo.id}")
                    handled = handled_clicks.get()
                    handled.add(btn_id)
                    handled_clicks.set(handled)
                    logger.debug(f"[MODAL] Triggered by {btn_id}, setting selected_repo_id={repo.id}")
                    selected_repo_id.set(repo.id)
                    ui.modal_show(
                        ui.modal(
                            ui.input_file("analysis_file", "Upload Excel Analysis (.xlsx)", accept=[".xlsx"]),
                            ui.input_action_button("submit_analysis_upload", "Submit"),
                            title="Upload Analysis",
                            easy_close=True
                        )
                    )
            except KeyError:
                continue

    @reactive.effect
    @reactive.event(input.submit_analysis_upload)
    def _handle_upload():
        user = current_user.get()
        repo_id = selected_repo_id.get()
        fileinfo = input.analysis_file()

        if not user or not fileinfo:
            ui.notification_show("Missing user or file.", type="error")
            return

        repo = next((r for r in user.repositories if r.id == repo_id), None)
        if not repo:
            ui.notification_show("Repository not found.", type="error")
            return

        # Save file
        upload_path = Path(data_dir) / user.username / repo.repo_name
        upload_path.mkdir(parents=True, exist_ok=True)
        filename = "analysis.xlsx"
        full_path = upload_path / filename

        # Remove old file if any
        if full_path.exists():
            full_path.unlink()

        shutil.copy(fileinfo[0]["datapath"], full_path)

        # Remove any old DB entry of type analysis for this repo
        db.query(Dataset).filter_by(
            repository_id=repo_id, dataset_type="analysis"
        ).delete()

        # Register in DB
        new_ds = Dataset(
            repository_id=repo_id,
            dataset_type="analysis",
            location=str(full_path.relative_to(data_dir))
        )
        db.add(new_ds)
        db.commit()

        ui.modal_remove()
        ui.notification_show("Analysis uploaded successfully.", type="message")

from shiny import reactive, ui
from server.state import current_user, selected_repo_id

def watch_edit_repo(input, db):
    @reactive.effect
    def _():
        user = current_user.get()
        if not user:
            return

        for repo in db.query(Repository).filter_by(user_id=user.id).all():
            btn_id = f"edit_repo_{repo.id}"
            try:
                if input[btn_id]() > 0 and btn_id not in handled_clicks.get():
                    logger.debug(f"[MODAL] Triggered by {btn_id}, setting selected_repo_id={repo.id}")
                    handled = handled_clicks.get()
                    handled.add(btn_id)
                    handled_clicks.set(handled)
                    logger.debug(f"[MODAL] Triggered by {btn_id}, setting selected_repo_id={repo.id}")
                    selected_repo_id.set(repo.id)
                    ui.modal_show(
                        ui.modal(
                            ui.input_text("edit_repo_name", "Repository Name", value=repo.repo_name),
                            ui.input_text("edit_repo_description", "Description", value=repo.description),
                            ui.input_select("edit_repo_visibility", "Visibility", {
                                "PRIVATE": "Private",
                                "EMBARGOED": "Embargoed",
                                "PUBLIC": "Public"
                            }, selected=repo.visibility.name),
                            ui.input_action_button("submit_repo_edit", "Save Changes"),
                            title=f"Edit Repository {repo.repo_name}",
                            easy_close=True
                        )
                    )
            except KeyError:
                continue

def handle_submit_repo_edit(input, db):
    @reactive.effect
    @reactive.event(input.submit_repo_edit)
    def _():
        user = current_user.get()
        repo_id = selected_repo_id.get()
        if not user or not repo_id:
            ui.notification_show("Missing user or repository context", type="error")
            return

        repo = db.query(Repository).filter_by(id=repo_id, user_id=user.id).first()
        if not repo:
            ui.notification_show("Repository not found", type="error")
            return

        # Update fields
        repo.repo_name = input.edit_repo_name()
        repo.description = input.edit_repo_description()
        repo.visibility = VisibilityEnum[input.edit_repo_visibility()]
        db.commit()

        ui.modal_remove()
        ui.notification_show("Repository updated successfully.", type="message")

def watch_repo_search(input):
    @reactive.effect
    @reactive.event(input.repo_search)
    def _update_search():
        search_query.set(input.repo_search())