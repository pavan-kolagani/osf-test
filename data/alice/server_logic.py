# from shiny import Inputs, Outputs, Session, reactive, render, ui
# from db.models import SessionLocal, Repository, VisibilityEnum, User, Dataset
# from sqlalchemy.orm.exc import NoResultFound


# current_user = reactive.Value(None)

# def server(input: Inputs, output: Outputs, session: Session):
#     db = SessionLocal()

#     def homepage_ui():
#         public_repos = db.query(Repository).filter(
#             Repository.visibility == VisibilityEnum.PUBLIC
#         ).order_by(Repository.created_at.desc()).all()

#         return ui.div(
#             ui.h3("Public Datasets"),
#             *[
#                 ui.card(
#                     ui.h4(repo.repo_name),
#                     ui.p(repo.description or "No description."),
#                     ui.p(f"Uploaded: {repo.created_at.strftime('%Y-%m-%d')}"),
#                     ui.input_action_button(f"open_repo_{repo.id}", "View Files")
#                 )
#                 for repo in public_repos
#             ]
#         )

#     @render.ui
#     def login_button_ui():
#         user = current_user.get()
#         if user is None:
#             return ui.input_action_button("login_btn", "Login as Scholar")
#         else:
#             return ui.div()  # hide button when logged in

#     @reactive.effect
#     def show_repo_modal():
#         for repo in db.query(Repository).filter(
#             Repository.visibility == VisibilityEnum.PUBLIC
#         ).all():
#             if input.get(f"open_repo_{repo.id}")():
#                 datasets = db.query(Dataset).filter(
#                     Dataset.repository_id == repo.id
#                 ).all()

#                 file_list = [ui.li(dataset.location) for dataset in datasets]
#                 ui.modal_show(
#                     ui.modal(
#                         ui.h4(f"Files in {repo.repo_name}"),
#                         ui.ul(*file_list),
#                         title="Repository Files",
#                         easy_close=True,
#                         footer=None
#                     )
#                 )
    
#     @reactive.effect
#     @reactive.event(input.login_btn)
#     def show_login_modal():
#         login_modal = ui.modal(
#             ui.input_text("username", "Username:"),
#             ui.input_password("password", "Password:"),
#             ui.input_action_button("submit_login", "Login"),
#             title="Scholar Login",
#             easy_close=True,
#             footer=None
#         )
#         ui.modal_show(login_modal)

#     @reactive.effect
#     @reactive.event(input.submit_login)
#     def process_login():
#         username = input.username()
#         password = input.password()
#         try:
#             user = db.query(User).filter_by(username=username, password_hash=password).one()
#             if user.role == 'scholar':
#                 current_user.set(user)
#                 ui.modal_remove()
#                 ui.notification_show("Login successful.", type="message")
#             else:
#                 ui.modal_remove()
#                 ui.notification_show("Access denied: Not a scholar.", type="error")
#         except NoResultFound:
#             ui.modal_remove()
#             ui.notification_show("Invalid credentials.", type="error")

#     def scholar_dashboard_ui():
#         user = current_user.get()
#         if not user or user.role != 'scholar':
#             return ui.div()

#         scholar_repos = db.query(Repository).filter(
#             Repository.user_id == user.id
#         ).order_by(Repository.created_at.desc()).all()

#         cards = [
#             ui.card(
#                 ui.h4(repo.repo_name),
#                 ui.p(repo.description or "No description."),
#                 ui.p(f"Created: {repo.created_at.strftime('%Y-%m-%d')}"),
#                 ui.input_action_button(f"edit_repo_{repo.id}", "Edit"),
#                 ui.input_action_button(f"upload_dataset_{repo.id}", "Upload Dataset"),
#                 ui.input_action_button(f"upload_analysis_{repo.id}", "Upload Analysis"),
#                 ui.input_action_button(f"toggle_visibility_{repo.id}", f"Set Visibility ({repo.visibility.name})")
#             )
#             for repo in scholar_repos
#         ]

#         return ui.div(
#         ui.h3(f"Welcome, {user.username}!"),
#         ui.p("Below are your repositories:"),
#         ui.hr(),
#         *cards,
#         ui.div(
#             ui.input_action_button("create_repo", "Create New Repository"),
#             class_="mt-3"
#         )
#     )




#     @reactive.effect
#     @reactive.event(input.create_repo)
#     def show_create_repo_modal():
#         ui.modal_show(
#             ui.modal(
#                 ui.input_text("new_repo_name", "Repository Name:"),
#                 ui.input_text("new_repo_description", "Description:"),
#                 ui.input_select("new_repo_visibility", "Visibility:", {
#                     "PRIVATE": "Private",
#                     "EMBARGOED": "Embargoed",
#                     "PUBLIC": "Public"
#                 }),
#                 ui.input_action_button("submit_new_repo", "Create"),
#                 title="Create New Repository",
#                 easy_close=True,
#                 footer=None
#             )
#         )
    
#     @reactive.effect
#     @reactive.event(input.submit_new_repo)
#     def create_new_repo():
#         repo_name = input.new_repo_name()
#         description = input.new_repo_description()
#         visibility = input.new_repo_visibility()

#         new_repo = Repository(
#             user_id=session.user.id,
#             repo_name=repo_name,
#             description=description,
#             visibility=VisibilityEnum[visibility]
#         )
#         db.add(new_repo)
#         db.commit()
#         ui.modal_remove()
#         ui.notification_show("Repository created successfully.", type="message")



#     @render.ui
#     def main_ui():
#         user = current_user.get()
#         print("Rendering main UI for user:", user.username if user else "None")
#         if user and user.role == 'scholar':
#             return scholar_dashboard_ui()
#         else:
#             return homepage_ui()






