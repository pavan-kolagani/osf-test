from shiny import ui, render
from db.models import Repository, VisibilityEnum, Dataset
from server.state import search_query

def homepage_ui(db):
    public_repos = db.query(Repository).filter(
        Repository.visibility == VisibilityEnum.PUBLIC
    ).order_by(Repository.created_at.desc()).all()

    return ui.div(
        ui.h3("Public Datasets"),
        *[
            ui.card(
                ui.h4(repo.repo_name),
                ui.p(repo.description or "No description."),
                ui.p(f"Uploaded: {repo.created_at.strftime('%Y-%m-%d')}"),
                ui.input_action_button(f"open_repo_{repo.id}", "View Files")
            ) for repo in public_repos
        ]
    )



def scholar_dashboard_ui(db, user):
    scholar_repos = db.query(Repository).filter(
        Repository.user_id == user.id
    ).order_by(Repository.created_at.desc()).all()

    @render.ui
    def filtered_cards():
        query = search_query.get().strip().lower()
        cards = []
        for repo in scholar_repos:
            if query and query not in repo.repo_name.lower():
                continue

            has_analysis = any(d.dataset_type == "analysis" for d in repo.datasets)

            permalink_url = None
            if has_analysis and repo.visibility in [VisibilityEnum.EMBARGOED, VisibilityEnum.PUBLIC]:
                permalink_url = f"/share/{repo.permalink}"

            card = ui.div(
                ui.card(
                    ui.card_header(ui.h5(repo.repo_name)),
                    ui.card_body(
                        ui.p(repo.description or "No description."),
                        ui.p(f"Created: {repo.created_at.strftime('%Y-%m-%d')}"),
                        ui.div(
                            ui.input_action_button(f"edit_repo_{repo.id}", "Edit", class_="btn btn-outline-primary me-2"),
                            ui.input_action_button(f"upload_analysis_{repo.id}", "Upload Analysis", class_="btn btn-outline-secondary"),
                            class_="d-flex flex-wrap gap-2 mt-2"
                        ),
                        ui.p(f"Permalink: {permalink_url}", class_="text-muted") if permalink_url else None
                    ),
                    class_="mb-3 shadow-sm"
                ),
                class_="col-md-6"
            )
            cards.append(card)

        return ui.div(
            ui.div(*cards, class_="row g-3")
        )

    return ui.div(
        ui.h3(f"Welcome, {user.username}!"),
        ui.div(
            ui.input_action_button("create_repo", "Create New Repository", class_="btn btn-success"),
            class_="mb-3"
        ),
        ui.input_text("repo_search", "Search repositories", placeholder="Enter repo name...", width="50%"),
        ui.hr(),
        ui.output_ui("filtered_cards")
    )