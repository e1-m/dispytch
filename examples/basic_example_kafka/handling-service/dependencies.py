class UserService:
    def __init__(self):
        self.users = []

    async def do_smth_with_the_user(self, user):
        print("Doing something with user", user)
        self.users.append(user)


def get_user_service():
    return UserService()
