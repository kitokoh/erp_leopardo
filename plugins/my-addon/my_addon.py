def main(context):
    user = context.get_current_user()
    context.notify("My Addon", f"Hello, {user['username']}!")
