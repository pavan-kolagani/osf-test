from shiny import ui
from db.models import Repository, Dataset, VisibilityEnum


def show_repo_modal(input, db):
    from .state import current_user
    import shiny.reactive as reactive

    @reactive.effect
    def _():
        for repo in db.query(Repository).filter(
            Repository.visibility == VisibilityEnum.PUBLIC
        ).all():

            if input[f"open_repo_{repo.id}"]() > 0:
                datasets = db.query(Dataset).filter(
                    Dataset.repository_id == repo.id
                ).all()
                ui.modal_show(
                    ui.modal(
                        ui.h4(f"Files in {repo.repo_name}"),
                        ui.tags.ul(*[ui.tags.li(d.location) for d in datasets]),
                        title="Repository Files",
                        easy_close=True
                    )
                )
